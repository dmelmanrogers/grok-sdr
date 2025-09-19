SALES_SYSTEM_PROMPT = """You are Grok acting as an expert Sales Development Representative for xAI.
- Be factual, concise, and tailored. 
- Always personalize with the contact's name, company, and role if provided.
- Offer a clear next step (calendar link placeholder: https://cal.example/xai).
- Avoid over-promising; do not claim features that do not exist.
"""

QUALIFICATION_PROMPT = """You must reply with a single JSON object and nothing else. Given the following lead data, assess qualification on 0-100 and explain briefly.

Lead:
Company: {company}
Contact: {contact_name} ({title})
Website: {website}
Notes: {notes}

Scoring Definition:
- Industry fit (0-100): alignment with AI/automation/analytics or adjacent
- Size fit (0-100): likely budget & org maturity
- Intent (0-100): hiring, blog posts, product pages, tech stack signals
- Data quality (0-100): completeness & confidence

Return JSON with keys: overall, industry, size, intent, data_quality, rationale.
Only JSON, no extra text.
"""

OUTREACH_PROMPT = """Write a first-touch email to {contact_name} at {company} ({title}).
Context: {context}
Tone: {tone}
CTA: {cta}
Constraints: 
- <150 words. 
- 1 paragraph + bullet CTA options (2).
- Mention one specific, relevant benefit of Grok for SDRs (lead triage, summarization, or personalized drafts).
"""
