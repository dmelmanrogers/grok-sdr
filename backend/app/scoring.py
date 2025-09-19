def weighted_score(parts, w):
    """
    parts: dict with numeric keys: industry, size, intent, data_quality
    w: object with attributes: industry_fit, size_fit, intent_signals, data_quality
    returns a 0-100 weighted score (float rounded to 2 decimals)
    """
    industry = float(parts.get("industry", 0))
    size = float(parts.get("size", 0))
    intent = float(parts.get("intent", 0))
    data_quality = float(parts.get("data_quality", 0))

    total_w = (w.industry_fit + w.size_fit + w.intent_signals + w.data_quality) or 1.0
    score = (
        industry * w.industry_fit +
        size * w.size_fit +
        intent * w.intent_signals +
        data_quality * w.data_quality
    ) / total_w
    return round(score, 2)
