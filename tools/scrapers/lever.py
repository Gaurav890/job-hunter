import logging
import requests
from models.job import Job
from tools.scrapers.base import title_match_score, is_us_location

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def scrape_lever(company_name: str, slug: str, target_titles: list[str]) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []

        jobs = []
        for item in data:
            title = (item.get("text") or "").strip()
            if not title:
                continue

            exact, close = title_match_score(title, target_titles)
            if not exact and not close:
                continue

            cats = item.get("categories") or {}
            all_locs = cats.get("allLocations") or []
            location = (
                all_locs[0] if all_locs
                else cats.get("location", "")
            )
            if not is_us_location(location):
                continue

            desc = (item.get("description") or "") + " " + (item.get("additional") or "")

            jobs.append(Job(
                company=company_name,
                title=title,
                location=location or "Unknown",
                url=item.get("hostedUrl", ""),
                source="Lever",
                description=desc,
                is_on_target_list=True,
            ))

        return jobs
    except Exception as e:
        logger.debug(f"Lever skip [{slug}]: {e}")
        return []
