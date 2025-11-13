thonimport json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .utils_location import normalize_location_text
from .company_parser import enrich_company_from_url

logger = logging.getLogger(__name__)

@dataclass
class JobSalary:
    text: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = None

@dataclass
class JobLocation:
    linkedin_text: Optional[str] = None
    parsed: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CompanyInfo:
    name: Optional[str] = None
    employee_count: Optional[int] = None
    linkedin_url: Optional[str] = None
    industries: List[str] = field(default_factory=list)
    logo_url: Optional[str] = None
    hq: Optional[str] = None

@dataclass
class JobPosting:
    id: str
    title: Optional[str]
    linkedin_url: str
    job_state: Optional[str] = None
    posted_date: Optional[datetime] = None
    description_text: Optional[str] = None
    description_html: Optional[str] = None
    location: JobLocation = field(default_factory=JobLocation)
    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None
    salary: JobSalary = field(default_factory=JobSalary)
    company: CompanyInfo = field(default_factory=CompanyInfo)
    benefits: List[str] = field(default_factory=list)
    applicants: Optional[int] = None
    views: Optional[int] = None
    apply_method: Optional[Dict[str, Any]] = None
    job_functions: List[str] = field(default_factory=list)
    expire_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        def encode(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        base = asdict(self)
        # Convert nested dataclasses already flattened by asdict, just need datetime conversion
        for k, v in list(base.items()):
            if isinstance(v, datetime):
                base[k] = encode(v)
        # Handle datetime nested in salary or other dicts if present
        def traverse(node: Any) -> Any:
            if isinstance(node, dict):
                return {kk: traverse(vv) for kk, vv in node.items()}
            if isinstance(node, list):
                return [traverse(x) for x in node]
            if isinstance(node, datetime):
                return node.isoformat()
            return node

        base = traverse(base)
        # Match the field names described in README
        mapped = {
            "id": self.id,
            "title": self.title,
            "linkedinUrl": self.linkedin_url,
            "jobState": self.job_state,
            "postedDate": base.get("posted_date"),
            "descriptionText": self.description_text,
            "descriptionHtml": self.description_html,
            "location": {
                "linkedinText": self.location.linkedin_text,
                "parsed": self.location.parsed,
            },
            "employmentType": self.employment_type,
            "workplaceType": self.workplace_type,
            "salary": base.get("salary"),
            "company": {
                "name": self.company.name,
                "employeeCount": self.company.employee_count,
                "linkedinUrl": self.company.linkedin_url,
                "industries": self.company.industries,
                "logoUrl": self.company.logo_url,
                "hq": self.company.hq,
            },
            "benefits": self.benefits,
            "applicants": self.applicants,
            "views": self.views,
            "applyMethod": self.apply_method,
            "jobFunctions": self.job_functions,
            "expireAt": base.get("expire_at"),
        }
        return mapped

class LinkedInJobParser:
    """
    Scrapes public LinkedIn job search results using only unauthenticated HTTP requests.

    This implementation is best-effort: LinkedIn can change their markup at any time.
    The parser attempts to read structured data blocks and falls back to simple selectors.
    """

    def __init__(self, settings: Dict[str, Any], session: Optional[requests.Session] = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        scraper_settings = settings.get("scraper", {})
        self.base_url = scraper_settings.get(
            "baseUrl", "https://www.linkedin.com/jobs/search/"
        )
        self.job_view_base = scraper_settings.get(
            "jobViewBaseUrl", "https://www.linkedin.com/jobs/view/"
        )
        self.user_agent = scraper_settings.get(
            "userAgent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36",
        )
        self.max_pages = int(scraper_settings.get("maxPages", 2))
        self.results_per_page = int(scraper_settings.get("resultsPerPage", 25))

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _build_search_params(
        self,
        query: str,
        location: str,
        page: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "keywords": query,
            "location": location,
            "refresh": "true",
            "position": "1",
            "pageNum": str(page),
        }
        filters = filters or {}

        # Experience level filter, LinkedIn expects numeric codes; we accept friendly labels and pass-through numbers
        experience = filters.get("experienceLevel")
        if experience:
            params["f_E"] = ",".join(
                str(x).strip() for x in (experience if isinstance(experience, Iterable) and not isinstance(experience, str) else [experience])
            )

        employment_type = filters.get("employmentType")
        if employment_type:
            params["f_JT"] = ",".join(
                str(x).strip() for x in (employment_type if isinstance(employment_type, Iterable) and not isinstance(employment_type, str) else [employment_type])
            )

        workplace_type = filters.get("workplaceType")
        if workplace_type:
            params["f_WT"] = ",".join(
                str(x).strip() for x in (workplace_type if isinstance(workplace_type, Iterable) and not isinstance(workplace_type, str) else [workplace_type])
            )

        date_posted = filters.get("datePosted")
        if date_posted:
            params["f_TPR"] = str(date_posted)

        industries = filters.get("industryIds")
        if industries:
            params["f_I"] = ",".join(str(x) for x in industries)

        easy_apply = filters.get("easyApply")
        if easy_apply:
            params["f_AL"] = "true"

        under_10_applicants = filters.get("underTenApplicants")
        if under_10_applicants:
            params["f_UD"] = "1"

        return params

    def _fetch_search_page(
        self, query: str, location: str, page: int, filters: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        params = self._build_search_params(query, location, page, filters)
        logger.debug("Requesting search page %s with params=%s", self.base_url, params)
        resp = self.session.get(self.base_url, params=params, headers=self._headers(), timeout=20)
        if resp.status_code != 200:
            logger.warning(
                "Search request failed (status=%s) for query=%r, location=%r, page=%d",
                resp.status_code,
                query,
                location,
                page,
            )
            return None
        return resp.text

    def _parse_job_snippets(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")

        results: List[Dict[str, Any]] = []

        # Primary attempt: LinkedIn often embeds job JSON in <code> tags as LD+JSON
        for code in soup.find_all("code"):
            type_attr = code.get("type", "")
            if "application/ld+json" not in type_attr:
                continue
            try:
                data = json.loads(code.string or "")
            except Exception:
                continue

            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                results.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        results.append(item)

        # Fallback: anchor tags with /jobs/view/ in href
        if not results:
            for anchor in soup.find_all("a", href=True):
                href = anchor["href"]
                if "/jobs/view/" not in href:
                    continue
                job_id = self._extract_job_id_from_url(href)
                if not job_id:
                    continue
                title = anchor.get_text(strip=True)
                snippet = {
                    "@type": "JobPosting",
                    "title": title,
                    "url": self._normalize_job_url(href),
                    "identifier": {"value": job_id},
                }
                results.append(snippet)

        return results

    def _extract_job_id_from_url(self, url: str) -> Optional[str]:
        # URLs usually look like /jobs/view/1234567890/ or contain digits followed by '/'
        import re

        match = re.search(r"/view/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"(\d+)", url)
        return match.group(1) if match else None

    def _normalize_job_url(self, url: str) -> str:
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            return f"https://www.linkedin.com{url}"
        if url.isdigit():
            return f"{self.job_view_base}{url}/"
        return f"{self.job_view_base}{url}"

    def _convert_snippet_to_job(self, snippet: Dict[str, Any]) -> JobPosting:
        identifier = snippet.get("identifier") or {}
        job_id = str(identifier.get("value") or identifier.get("@id") or "")
        if not job_id:
            job_id = self._extract_job_id_from_url(snippet.get("url", "")) or ""

        url = snippet.get("url") or self._normalize_job_url(job_id)
        title = snippet.get("title")

        date_posted_raw = snippet.get("datePosted")
        posted_date = None
        if date_posted_raw:
            try:
                posted_date = date_parser.parse(date_posted_raw)
            except Exception:
                posted_date = None

        employment_type = snippet.get("employmentType")
        description_html = snippet.get("description")
        description_text = None
        if description_html:
            text_soup = BeautifulSoup(description_html, "lxml")
            description_text = text_soup.get_text("\n", strip=True)

        hiring_org = snippet.get("hiringOrganization") or {}
        company = CompanyInfo(
            name=hiring_org.get("name"),
            linkedin_url=hiring_org.get("sameAs"),
        )

        job_location_raw = None
        loc_field = snippet.get("jobLocation")
        if isinstance(loc_field, dict):
            job_location_raw = loc_field.get("address", {}).get("addressLocality")
        elif isinstance(loc_field, list) and loc_field:
            maybe = loc_field[0]
            if isinstance(maybe, dict):
                job_location_raw = maybe.get("address", {}).get("addressLocality")

        location = JobLocation(
            linkedin_text=job_location_raw,
            parsed=normalize_location_text(job_location_raw or ""),
        )

        salary_info = snippet.get("baseSalary") or {}
        salary = JobSalary()
        if salary_info:
            value = salary_info.get("value") or {}
            try:
                salary.min = float(value.get("minValue")) if value.get("minValue") else None
            except (TypeError, ValueError):
                salary.min = None
            try:
                salary.max = float(value.get("maxValue")) if value.get("maxValue") else None
            except (TypeError, ValueError):
                salary.max = None
            salary.currency = salary_info.get("currency")
            if salary.min or salary.max:
                bounds = []
                if salary.min is not None:
                    bounds.append(f"{salary.min:,.0f}")
                if salary.max is not None:
                    bounds.append(f"{salary.max:,.0f}")
                salary.text = " - ".join(bounds)
                if salary.currency:
                    salary.text += f" {salary.currency}"

        expire_at_raw = snippet.get("validThrough")
        expire_at = None
        if expire_at_raw:
            try:
                expire_at = date_parser.parse(expire_at_raw)
            except Exception:
                expire_at = None

        job = JobPosting(
            id=job_id,
            title=title,
            linkedin_url=url,
            job_state="LISTED",
            posted_date=posted_date,
            description_text=description_text,
            description_html=description_html,
            location=location,
            employment_type=employment_type,
            salary=salary,
            company=company,
            expire_at=expire_at,
        )
        return job

    def search_jobs(
        self,
        query: str,
        location: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[JobPosting]:
        logger.info(
            "Searching jobs for query=%r, location=%r, max_results=%d",
            query,
            location,
            max_results,
        )
        collected: List[JobPosting] = []
        seen_ids: set[str] = set()

        current_page = 0
        while len(collected) < max_results and current_page < self.max_pages:
            html = self._fetch_search_page(query, location, current_page, filters)
            if not html:
                break

            snippets = self._parse_job_snippets(html)
            if not snippets:
                logger.info("No job snippets parsed on page %d, stopping.", current_page)
                break

            for snippet in snippets:
                if snippet.get("@type") != "JobPosting":
                    continue
                job = self._convert_snippet_to_job(snippet)
                if not job.id or job.id in seen_ids:
                    continue
                seen_ids.add(job.id)
                collected.append(job)
                if len(collected) >= max_results:
                    break

            current_page += 1

        logger.info("Search produced %d unique job(s).", len(collected))
        return collected

    def _fetch_job_details(self, job_url: str) -> Dict[str, Any]:
        logger.debug("Fetching job details from %s", job_url)
        resp = self.session.get(job_url, headers=self._headers(), timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"Job detail request failed with status {resp.status_code}: {job_url}")

        html = resp.text
        soup = BeautifulSoup(html, "lxml")

        # Try to get JSON-LD JobPosting block again
        structured_data: Dict[str, Any] | None = None
        for code in soup.find_all("code"):
            if "application/ld+json" not in (code.get("type") or ""):
                continue
            try:
                data = json.loads(code.string or "")
            except Exception:
                continue
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                structured_data = data
                break
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        structured_data = item
                        break
            if structured_data:
                break

        if not structured_data:
            structured_data = {}

        # Description
        description_html = structured_data.get("description")
        description_text = None
        if description_html:
            text_soup = BeautifulSoup(description_html, "lxml")
            description_text = text_soup.get_text("\n", strip=True)
        else:
            # Fallback: select common description container
            desc = soup.find("div", attrs={"class": lambda c: c and "description" in c})
            if desc:
                description_html = str(desc)
                description_text = desc.get_text("\n", strip=True)

        # Applicants/views info is sometimes embedded in meta or span elements; best-effort scraping
        applicants = None
        views = None
        for span in soup.find_all("span"):
            text = span.get_text(strip=True)
            if "applicant" in text.lower():
                try:
                    applicants = int("".join(ch for ch in text if ch.isdigit()))
                except ValueError:
                    pass
            if "view" in text.lower():
                try:
                    views = int("".join(ch for ch in text if ch.isdigit()))
                except ValueError:
                    pass

        # Job functions, benefits
        job_functions: List[str] = []
        benefits: List[str] = []
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if not text:
                continue
            if "benefit" in text.lower():
                benefits.append(text)
            if "function" in text.lower():
                job_functions.append(text)

        # Apply method: capture the primary apply button href
        apply_method: Dict[str, Any] | None = None
        for button in soup.find_all("a", href=True):
            btn_text = button.get_text(strip=True).lower()
            if "apply" in btn_text:
                apply_method = {"url": button["href"], "label": button.get_text(strip=True)}
                break

        # Company enrichment if we can find a link
        company_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/company/" in href:
                if href.startswith("http"):
                    company_url = href
                else:
                    company_url = f"https://www.linkedin.com{href}"
                break

        company_info: Dict[str, Any] | None = None
        if company_url:
            try:
                company_info = enrich_company_from_url(self.session, company_url)
            except Exception as exc:
                logger.warning("Company enrichment failed for %s: %s", company_url, exc)

        details: Dict[str, Any] = {
            "descriptionHtml": description_html,
            "descriptionText": description_text,
            "applicants": applicants,
            "views": views,
            "jobFunctions": job_functions,
            "benefits": benefits,
            "applyMethod": apply_method,
        }
        if company_info:
            details["company"] = company_info
        return details

    def fetch_job_details_safe(self, job_url: str, base_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wraps _fetch_job_details with error handling so runner can continue.
        """
        try:
            details = self._fetch_job_details(job_url)
            merged = {**base_job, **{k: v for k, v in details.items() if v is not None}}
            return merged
        except Exception as exc:
            logger.warning("Failed to fetch/enrich job details for %s: %s", job_url, exc)
            return base_job