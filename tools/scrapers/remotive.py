import logging
import requests
from models.job import Job
from tools.scrapers.base import title_match_score

logger = logging.getLogger(__name__)

API = "https://remotive.com/api/remote-jobs"
CATEGORIES = ["product", "management-finance", "all-others"]


def scrape_remotive(target_titles: list[str]) -> list[Job]:
    jobs = []
    seen: set[str] = set()

    for category in CATEGORIES:
        try:
            resp = requests.get(API, params={"category": category, "limit": 100}, timeout=10)
            if resp.status_code != 200:
                continue
            for item in resp.json().get("jobs", []):
                title = (item.get("title") or "").strip()
                exact, close = title_match_score(title, target_titles)
                if not exact and not close:
                    continue

                url = item.get("url") or ""
                if not url or url in seen:
                    continue
                seen.add(url)

                company = item.get("company_name") or "Unknown"
                location = item.get("candidate_required_location") or "Remote"

                jobs.append(Job(
                    company=company,
                    title=title,
                    location=location,
                    url=url,
                    source="Remotive",
                    description=item.get("description") or "",
                    posted_date=(item.get("publication_date") or "")[:10],
                    is_on_target_list=False,
                ))
        except Exception as e:
            logger.debug(f"Remotive [{category}] skip: {e}")

    logger.info(f"Remotive: {len(jobs)} matching jobs")
    return jobs
