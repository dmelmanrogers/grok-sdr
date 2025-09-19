import os, time, json
import requests
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

XAI_API_KEY = os.getenv("XAI_API_KEY")
BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai")
MODEL = os.getenv("XAI_MODEL", "grok-4-latest") 

HEADERS = {
    "Authorization": f"Bearer {XAI_API_KEY}" if XAI_API_KEY else "",
    "Content-Type": "application/json"
}

# Of note: xAI provides both chat completions (/v1/chat/completions) and a stateful Responses API (/v1/responses).
# We will use chat completions here for simplicity; see xAI API reference and guides.

def chat(messages: List[Dict], temperature: float = 0.3, max_tokens: int = 400):
    """
    Calls xAI /v1/chat/completions.
    - Uses max_output_tokens (xAI style) instead of max_tokens.
    - Never raises on HTTP 200; returns "" if no content so caller can fallback.
    """
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY not set")
    url = f"{BASE_URL}/v1/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_output_tokens": max_tokens,  # <-- here we can use xAI-style param
    }

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        except Exception as e:
            print(f"[GROK HTTP ERROR attempt {attempt+1}] {e}")
            time.sleep(1.5 * (attempt + 1))
            continue

        # Debugging handling: show first 400 chars of body
        print(f"[GROK HTTP {resp.status_code}] {resp.text[:400]!r}")

        if resp.status_code == 200:
            # Try compatible shape
            try:
                data = resp.json()
                content = data["choices"][0]["message"].get("content", "")
                # if empty, let caller fallback; don't throw
                return content or ""
            except Exception:
                pass
            # Try /v1/responses-like shape
            try:
                data = resp.json()
                return data.get("output_text", "")  # may be ""
            except Exception:
                # return raw text so caller can try to parse
                return resp.text

        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(1.5 * (attempt + 1))
            continue

        # Non-retryable error: surface it
        raise RuntimeError(f"Grok API error {resp.status_code}: {resp.text}")

    raise RuntimeError("Grok API retry limit exceeded")


def respond(input_text: str, temperature: float = 0.3, max_output_tokens: int = 400):
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY not set")
    url = f"{BASE_URL}/v1/responses"
    payload = {
        "model": MODEL,
        "input": input_text,
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print(f"[GROK RESPONSES {resp.status_code}] {resp.text[:400]!r}")
    resp.raise_for_status()
    data = resp.json()
    return data.get("output_text") or resp.text
