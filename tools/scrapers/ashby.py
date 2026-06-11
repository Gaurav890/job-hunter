import logging
import requests
from models.job import Job
from tools.scrapers.base import title_match_score, is_us_location

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def scrape_ashby(company_name: str, slug: str, target_titles: list[str]) -> list[Job]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        if resp.status_code != 200:
            return []

        data = resp.json()
        # Ashby returns jobs under different keys depending on version
        items = (
            data.get("jobs")
            or data.get("jobPostings")
            or (data.get("results") or {}).get("jobPostings")
            or (data.get("results") or {}).get("jobs")
            or []
        )

        jobs = []
        for item in items:
            title = (item.get("title") or item.get("name") or "").strip()
            if not title:
                continue

            exact, close = title_match_score(title, target_titles)
            if not exact and not close:
                continue

            # Location can be nested or flat
            loc = item.get("locationName") or item.get("location") or ""
            if isinstance(loc, dict):
                loc = loc.get("name") or loc.get("locationName") or ""
            if item.get("isRemote"):
                loc = loc or "Remote"

            if not is_us_location(loc):
                continue

            job_url = (
                item.get("externalLink")
                or item.get("hostedUrl")
                or item.get("applyUrl")
                or f"https://jobs.ashbyhq.com/{slug}"
            )
            description = item.get("descriptionHtml") or item.get("description") or ""
            posted = (item.get("publishedAt") or item.get("postedAt") or "")[:10]

            jobs.append(Job(
                company=company_name,
                title=title,
                location=loc or "Unknown",
                url=job_url,
                source="Ashby",
                description=description,
                posted_date=posted,
                is_on_target_list=True,
            ))

        return jobs
    except Exception as e:
        logger.debug(f"Ashby skip [{slug}]: {e}")
        return []
