# Grok-Powered SDR

## Project Title
**Grok-Powered SDR** — an AI-assisted Sales Development Representative system.

---

## Description
The goal of our Grok-Powered SDR here is to create a lightweight web app that streamlines early-stage sales workflows. It lets teams:
- **Qualify leads** using model-generated component scores and a weighted overall score.
- **Draft personalized outreach** emails in one click.
- **Coordinate meetings** by logging proposed times/links and advancing pipeline stages.
- **Evaluate prompts** with a small, extensible harness to keep generations on-spec.

We want a fast, demo-friendly workflow with clear data handling, strict JSON for scoring, and a simple UI.

---

## Features
- **Lead Management & Pipeline**
  - Stages: `new → qualified → contacted → meeting → won/lost`
  - Search by company/contact/notes
  - Activity timeline & message history
- **AI Qualification**
  - Strict-JSON scoring with sanitizer & repair pass
  - Adjustable weights: industry, size, intent, data quality
  - Auto-advance to `qualified` when score ≥ 60
- **Personalized Outreach**
  - One-click first-touch email (tone / CTA / extra context)
- **Meeting Coordination**
  - Quick form logs proposed time + calendar link and sets stage to `meeting`
- **Eval Harness**
  - `/evals/run` scenarios (e.g., personalization, length, placeholder checks)
  - Pass/fail table to guide prompt iteration
- **Reproducible Dev**
  - Dockerfile + docker-compose for one-command startup

---

## Installation

### Prerequisites
- Python **3.11+**
- (Optional) Docker & Docker Compose

### Local Setup
```bash
# clone and enter
git clone <REPO_URL> grok-sdr
cd grok-sdr

# python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

### Run (Dev)
```bash
cd backend
uvicorn app.main:app --reload
# open http://localhost:8000
```

### Run (Docker)
```bash
docker compose up --build
# open http://localhost:8000
```

---

## Usage

### Web UI Workflow
1. **Add a lead** on the home page (right card), then click the new row to open it.
2. **Score lead** — click **Run with Grok**.  
   The app requests strict-JSON component scores, applies your weights, sets stage to `qualified` if ≥ 60, and logs an activity.
3. **Draft outreach** — set tone/CTA/extra context and click **Draft Email**.  
   The generated email appears under **Messages**; **Activity** records the event.
4. **Schedule meeting** — enter a proposed time and calendar link; submit to auto-set stage to `meeting` and log an activity.
5. **Run quick evals** — click **Run** in **Quick Evals** to see pass/fail for common prompt constraints.

### API (Selected Endpoints)
Interactive docs at `http://localhost:8000/docs`.

- `POST /leads` — create a lead  
- `GET  /lead/{id}` — fetch a lead  
- `POST /lead/{id}/score` — score with Grok (form fields for weights)  
- `POST /lead/{id}/message` — generate first-touch email (form fields)  
- `POST /lead/{id}/stage` — change pipeline stage  
- `POST /lead/{id}/meeting` — log proposed time + link and set stage  
- `POST /evals/run` — run eval scenarios and return an HTML table

---