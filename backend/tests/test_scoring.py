from app.scoring import weighted_score
from types import SimpleNamespace

def test_weights_normalize():
    w = SimpleNamespace(industry_fit=1, size_fit=0, intent_signals=0, data_quality=0)
    parts = {"industry":50}
    assert weighted_score(parts, w) == 50.0
