import json
from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from .db import Base, engine, get_db, now_utc
from . import models, schemas
from .grok_client import chat, respond
from .prompts import SALES_SYSTEM_PROMPT, QUALIFICATION_PROMPT, OUTREACH_PROMPT
from .scoring import weighted_score

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Grok SDR Demo")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/templates"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    leads = db.query(models.Lead)
    if q:
        qlike = f"%{q}%"
        leads = leads.filter(
            (models.Lead.company.ilike(qlike)) |
            (models.Lead.contact_name.ilike(qlike)) |
            (models.Lead.notes.ilike(qlike))
        )
    leads = leads.order_by(models.Lead.updated_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "leads": leads, "q": q or ""})

@app.post("/leads", response_class=RedirectResponse)
def create_lead(
    company: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    title: str = Form(""),
    website: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    lead = models.Lead(company=company, contact_name=contact_name, email=email, title=title, website=website, notes=notes)
    db.add(lead)
    db.commit(); db.refresh(lead)
    _log(db, lead.id, "created", f"Lead created for {contact_name} at {company}")
    return RedirectResponse(url=f"/lead/{lead.id}", status_code=303)

@app.get("/lead/{lead_id}", response_class=HTMLResponse)
def lead_detail(lead_id: int, request: Request, db: Session = Depends(get_db)):
    lead = db.get(models.Lead, lead_id)
    if not lead:
        return HTMLResponse("Lead not found", status_code=404)
    return templates.TemplateResponse("lead_detail.html", {"request": request, "lead": lead})

def _log(db: Session, lead_id: int, t: str, detail: str):
    db.add(models.Activity(lead_id=lead_id, type=t, detail=detail))
    db.commit()

@app.post("/lead/{lead_id}/score", response_class=HTMLResponse)
def score_lead(
    lead_id: int,
    industry_fit: float = Form(0.4),
    size_fit: float = Form(0.2),
    intent_signals: float = Form(0.3),
    data_quality: float = Form(0.1),
    db: Session = Depends(get_db),
):
    lead = db.get(models.Lead, lead_id)
    if not lead:
        return HTMLResponse("Lead not found", status_code=404)

    # weights from the form
    weights = schemas.ScoreWeights(
        industry_fit=industry_fit,
        size_fit=size_fit,
        intent_signals=intent_signals,
        data_quality=data_quality,
    )

    # build the user prompt from the template
    user_prompt = QUALIFICATION_PROMPT.format(
        company=lead.company,
        contact_name=lead.contact_name,
        title=lead.title or "Unknown",
        website=lead.website or "N/A",
        notes=lead.notes or "N/A",
    )

    # ---- CALL GROK (primary: chat, fallback: responses) ----
    content = chat(
        [{"role": "system", "content": SALES_SYSTEM_PROMPT},
         {"role": "user", "content": user_prompt}],
        temperature=0.0, max_tokens=300
    )
    if not content or not content.strip():
        # fallback to /v1/responses if chat returns nothing
        content = respond(
            "You are an SDR assistant. Reply with ONLY one JSON object with keys: "
            "overall, industry, size, intent, data_quality, rationale.\n\n"
            f"{user_prompt}",
            temperature=0.0, max_output_tokens=300
        )

    print("\n=== RAW QUALIFICATION OUTPUT (attempt 1) ===\n", (content or "")[:800], "\n")

    # ---- PARSE (with tiny sanitizer + repair retry) ----
    def _try_parse(text: str):
        t = (text or "").strip()
        if t.startswith("```"):
            # strip code fences like ```json ... ```
            t = t.strip("`")
            if t.lower().startswith("json"):
                t = t[4:].strip()
        return json.loads(t)

    try:
        data = _try_parse(content)
    except Exception:
        repair = (
            "Convert the following to a single JSON object with keys: "
            "overall, industry, size, intent, data_quality, rationale. "
            "Return ONLY JSON and nothing else.\n\n"
            f"{content}"
        )
        content2 = chat(
            [{"role": "system", "content": "Return ONLY a JSON object."},
             {"role": "user", "content": repair}],
            temperature=0.0, max_tokens=200
        )
        print("\n=== RAW QUALIFICATION OUTPUT (attempt 2) ===\n", (content2 or "")[:800], "\n")
        try:
            data = _try_parse(content2)
        except Exception:
            _log(db, lead.id, "scored", "Model returned non-JSON twice")
            return HTMLResponse("<div>Scoring failed (non-JSON). Try again.</div>", status_code=502)

    # ---- SCORE + SAVE ----
    parts = {
        "industry": float(data.get("industry", 0)),
        "size": float(data.get("size", 0)),
        "intent": float(data.get("intent", 0)),
        "data_quality": float(data.get("data_quality", 0)),
    }
    lead.score = weighted_score(parts, weights)
    lead.stage = "qualified" if lead.score >= 60 else "new"
    lead.updated_at = now_utc()


    db.commit(); db.refresh(lead)
    _log(db, lead.id, "scored", f"Parts={parts} -> weighted={lead.score}. Rationale: {str(data.get('rationale',''))[:220]}")
    return f"<div><b>Score:</b> {lead.score:.0f} &nbsp; <span class='pill'>{lead.stage}</span></div>"


@app.post("/lead/{lead_id}/message", response_class=HTMLResponse)
def generate_message(
    lead_id: int,
    tone: str = Form("concise, helpful, human"),
    call_to_action: str = Form("Would you be open to a 20-minute intro call this week?"),
    extra_context: str = Form(None),
    db: Session = Depends(get_db),
):
    lead = db.get(models.Lead, lead_id)
    if not lead:
        return HTMLResponse("Lead not found", status_code=404)

    prompt = OUTREACH_PROMPT.format(
        contact_name=lead.contact_name, company=lead.company,
        title=lead.title or "Unknown",
        context=extra_context or lead.notes or "No extra context",
        tone=tone, cta=call_to_action
    )
    content = chat(
        [{"role": "system", "content": SALES_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}],
        temperature=0.4, max_tokens=300
    )
    msg = models.Message(lead_id=lead.id, role="assistant", content=content)
    db.add(msg)
    lead.stage = "contacted"
    lead.updated_at = now_utc()
    db.commit(); db.refresh(lead)
    _log(db, lead.id, "messaged", "Generated outreach email")
    return f"<pre>{content}</pre>"


@app.post("/lead/{lead_id}/meeting", response_class=HTMLResponse)
def schedule_meeting(
    lead_id: int,
    when: str = Form("Next Tue 2pm CT"),
    link: str = Form("https://cal.example/xai"),
    db: Session = Depends(get_db),
):
    lead = db.get(models.Lead, lead_id)
    if not lead:
        return HTMLResponse("Lead not found", status_code=404)
    lead.stage = "meeting"
    lead.updated_at = now_utc()
    db.add(models.Activity(lead_id=lead.id, type="meeting", detail=f"Proposed: {when} — {link}"))
    db.commit()
    return RedirectResponse(url=f"/lead/{lead_id}", status_code=303)


@app.post("/lead/{lead_id}/stage")
def update_stage(lead_id: int, stage: str = Form(...), db: Session = Depends(get_db)):
    lead = db.get(models.Lead, lead_id)
    if not lead: return JSONResponse({"error":"not found"}, status_code=404)
    lead.stage = stage; lead.updated_at = now_utc()
    db.commit()
    _log(db, lead.id, "stage_change", f"Stage -> {stage}")
    return RedirectResponse(url=f"/lead/{lead_id}", status_code=303)

@app.post("/evals/run", response_class=HTMLResponse)
def run_evals(db: Session = Depends(get_db)):
    scenarios = [
        {"name":"Personalization", "prompt":"Write a 1-paragraph first-touch email to Jane at Contoso about AI SDR automation.", "must_include":"Jane", "must_not_include":"[[FILL]"},
        {"name":"LengthLimit", "prompt":"In <=120 words, pitch Grok SDR benefits for a data infra startup.", "must_include":"Grok"},
    ]
    rows = []
    for sc in scenarios:
        out = chat([
            {"role":"system","content":SALES_SYSTEM_PROMPT},
            {"role":"user","content": sc["prompt"]}
        ], temperature=0.3, max_tokens=250)
        ok, notes = True, []
        if sc.get("must_include") and sc["must_include"] not in out:
            ok = False; notes.append("missing personalization")
        if sc.get("must_not_include") and sc["must_not_include"] in out:
            ok = False; notes.append("placeholder leaked")
        if len(out.split()) > 130 and "120" in sc["prompt"]:
            ok = False; notes.append("over length")
        rows.append((sc["name"], "pass" if ok else "fail", "; ".join(notes) or "pass"))

    # Simple HTML table for HTMX target
    html = [
        '<table style="width:100%;border-collapse:collapse;font:14px system-ui">',
        '<tr><th style="text-align:left;border-bottom:1px solid #eee;padding:6px">Scenario</th>',
        '<th style="text-align:left;border-bottom:1px solid #eee;padding:6px">Result</th>',
        '<th style="text-align:left;border-bottom:1px solid #eee;padding:6px">Notes</th></tr>'
    ]
    for name, res, note in rows:
        color = "#198754" if res=="pass" else "#dc3545"
        html.append(
            f'<tr><td style="padding:6px;border-bottom:1px solid #f3f3f3">{name}</td>'
            f'<td style="padding:6px;border-bottom:1px solid #f3f3f3;color:{color}">{res}</td>'
            f'<td style="padding:6px;border-bottom:1px solid #f3f3f3">{note}</td></tr>'
        )
    html.append("</table>")
    return HTMLResponse("".join(html))
