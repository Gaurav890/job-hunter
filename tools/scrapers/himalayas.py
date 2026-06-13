import logging
import requests
from models.job import Job
from tools.scrapers.base import title_match_score, is_us_location

logger = logging.getLogger(__name__)

API = "https://himalayas.app/jobs/api"
KEYWORDS = [
    "AI product manager",
    "technical product manager",
    "forward deployed engineer",
    "AI solutions engineer",
    "agent strategist",
]


def scrape_himalayas(target_titles: list[str]) -> list[Job]:
    jobs = []
    seen: set[str] = set()

    for kw in KEYWORDS:
        try:
            resp = requests.get(API, params={"q": kw, "limit": 100}, timeout=10)
            if resp.status_code != 200:
                continue
            for item in resp.json().get("jobs", []):
                title = (item.get("title") or "").strip()
                exact, close = title_match_score(title, target_titles)
                if not exact and not close:
                    continue

                url = item.get("url") or item.get("applicationUrl") or ""
                if not url or url in seen:
                    continue
                seen.add(url)

                company = (item.get("company") or {}).get("name") or item.get("companyName") or "Unknown"
                location = item.get("location") or "Remote"
                if not is_us_location(location) and "remote" not in location.lower():
                    continue

                jobs.append(Job(
                    company=company,
                    title=title,
                    location=location,
                    url=url,
                    source="Himalayas",
                    description=item.get("description") or "",
                    posted_date=(item.get("createdAt") or item.get("publishedAt") or "")[:10],
                    is_on_target_list=False,
                ))
        except Exception as e:
            logger.debug(f"Himalayas [{kw}] skip: {e}")

    logger.info(f"Himalayas: {len(jobs)} matching jobs")
    return jobs
