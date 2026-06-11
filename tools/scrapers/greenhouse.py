import logging
import requests
from models.job import Job
from tools.scrapers.base import title_match_score, is_us_location

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def scrape_greenhouse(company_name: str, slug: str, target_titles: list[str]) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        if resp.status_code != 200:
            return []

        jobs = []
        for item in resp.json().get("jobs", []):
            title = (item.get("title") or "").strip()
            if not title:
                continue

            exact, close = title_match_score(title, target_titles)
            if not exact and not close:
                continue

            loc = item.get("location") or {}
            location = loc.get("name", "") if isinstance(loc, dict) else str(loc)
            if not is_us_location(location):
                continue

            jobs.append(Job(
                company=company_name,
                title=title,
                location=location or "Unknown",
                url=item.get("absolute_url", ""),
                source="Greenhouse",
                description=item.get("content", ""),
                posted_date=(item.get("updated_at") or "")[:10],
                is_on_target_list=True,
            ))

        return jobs
    except Exception as e:
        logger.debug(f"Greenhouse skip [{slug}]: {e}")
        return []
