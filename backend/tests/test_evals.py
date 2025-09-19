from app.scoring import weighted_score
from types import SimpleNamespace

def test_weighted_score():
    w = SimpleNamespace(industry_fit=0.4, size_fit=0.2, intent_signals=0.3, data_quality=0.1)
    parts = {"industry":80,"size":60,"intent":70,"data_quality":90}
    assert weighted_score(parts, w) > 70
