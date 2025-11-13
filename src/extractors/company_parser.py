thonimport logging
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def _parse_employee_count(text: str) -> Optional[int]:
    # best-effort parsing like "11-50 employees" or "34 employees"
    digits = "".join(ch if ch.isdigit() or ch == "-" else " " for ch in text)
    parts = [p for p in digits.split() if p]
    if not parts:
        return None
    # take the largest numeric chunk as a rough indicator
    numbers = []
    for part in parts:
        try:
            numbers.append(int(part))
        except ValueError:
            continue
    return max(numbers) if numbers else None

def enrich_company_from_url(session: requests.Session, company_url: str) -> Dict[str, Any]:
    """
    Fetches a LinkedIn company profile page and extracts lightweight company information.

    This function does not require authentication but is sensitive to LinkedIn layout changes;
    it uses tolerant selectors and fails gracefully.
    """
    logger.debug("Enriching company from %s", company_url)
    resp = session.get(company_url, headers={"User-Agent": session.headers.get("User-Agent", "")}, timeout=20)
    if resp.status_code != 200:
        logger.warning("Company request failed with status %s for %s", resp.status_code, company_url)
        return {
            "name": None,
            "employeeCount": None,
            "linkedinUrl": company_url,
            "industries": [],
            "logoUrl": None,
            "hq": None,
        }

    soup = BeautifulSoup(resp.text, "lxml")

    # Company name
    name_tag = soup.find("h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    # Employee count & HQ often appear in <dl>/<dd> or simple spans; we scan for clues
    employee_count = None
    hq = None
    industries: list[str] = []

    for text_node in soup.find_all(text=True):
        text = text_node.strip()
        lower = text.lower()
        if "employees" in lower and employee_count is None:
            employee_count = _parse_employee_count(text)
        if ("headquarters" in lower or "hq" in lower) and hq is None:
            # parent may contain the actual location text
            parent_text = text_node.parent.get_text(" ", strip=True)
            hq = parent_text.replace("Headquarters", "").replace("HQ", "").strip()

    # Industries sometimes presented as a list of links with "industry" in surrounding text
    for a in soup.find_all("a"):
        if not a.get_text(strip=True):
            continue
        parent_text = a.parent.get_text(" ", strip=True).lower()
        if "industry" in parent_text and a.get_text(strip=True) not in industries:
            industries.append(a.get_text(strip=True))

    # Logo URL from img tags with alt containing company name
    logo_url = None
    if name:
        for img in soup.find_all("img"):
            alt = img.get("alt") or ""
            if name.lower() in alt.lower():
                logo_url = img.get("src")
                break

    return {
        "name": name,
        "employeeCount": employee_count,
        "linkedinUrl": company_url,
        "industries": industries,
        "logoUrl": logo_url,
        "hq": hq,
    }