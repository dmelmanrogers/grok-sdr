"""
Evals helper module.

Currently, the main eval logic is implemented directly in main.py under
the /evals/run endpoint. This file is reserved per (what I understand of)
best practices for hypothetical future reusable evaluation functions
or scenario definitions.
"""

from typing import Dict, List

def basic_eval(output: str, must_include: str = None,
               must_not_include: str = None,
               max_words: int = None) -> Dict:
    """
    Run simple checks on model output.
    Returns a dict with keys: ok, notes.
    """
    ok = True
    notes = []

    if must_include and must_include not in output:
        ok = False
        notes.append(f"missing '{must_include}'")

    if must_not_include and must_not_include in output:
        ok = False
        notes.append(f"should not include '{must_not_include}'")

    if max_words is not None and len(output.split()) > max_words:
        ok = False
        notes.append(f"too long ({len(output.split())}>{max_words})")

    return {"ok": ok, "notes": "; ".join(notes) if notes else "pass"}
