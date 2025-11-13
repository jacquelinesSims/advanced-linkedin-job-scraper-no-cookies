thonfrom typing import Any, Dict

def normalize_location_text(linkedin_text: str) -> Dict[str, Any]:
    """
    Lightweight location parser that turns a LinkedIn location string into a structured object.

    It does not call any external geocoding API; instead it heuristically splits the string
    into city, state/region, and country when possible.

    Examples:
        "Greenwood Village, CO"               -> city="Greenwood Village", state="CO"
        "London, England, United Kingdom"     -> city="London", state="England", country="United Kingdom"
        "Remote"                              -> parsed.text="Remote"
    """
    parsed: Dict[str, Any] = {
        "text": linkedin_text or "",
        "city": None,
        "state": None,
        "country": None,
    }

    if not linkedin_text:
        return parsed

    text = linkedin_text.strip()
    parts = [p.strip() for p in text.split(",") if p.strip()]

    if len(parts) == 1:
        # Could be city or just "Remote"
        if text.lower() == "remote":
            parsed["city"] = None
            parsed["state"] = None
            parsed["country"] = None
        else:
            parsed["city"] = text
        return parsed

    if len(parts) == 2:
        parsed["city"], parsed["state"] = parts
        return parsed

    # 3 or more parts: assume city, state/region, country
    parsed["city"] = parts[0]
    parsed["state"] = parts[1]
    parsed["country"] = parts[-1]
    return parsed