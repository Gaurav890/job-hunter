import time
import logging

from models.job import Job
from tools.scrapers.greenhouse import scrape_greenhouse
from tools.scrapers.lever import scrape_lever
from tools.scrapers.company_direct import scrape_company_direct
from tools.scrapers.career_url_discovery import discover_careers_url

logger = logging.getLogger(__name__)


class DiscoveryCrew:
    def __init__(self, companies: list[dict], target_titles: list[str]):
        self.companies = companies
        self.target_titles = target_titles

    def _add_jobs(self, new_jobs: list[Job], all_jobs: list[Job], seen_urls: set[str]) -> None:
        for job in new_jobs:
            if job.url and job.url not in seen_urls:
                seen_urls.add(job.url)
                all_jobs.append(job)

    def run(self) -> tuple[list[Job], int]:
        """Returns (jobs, companies_checked)."""
        all_jobs: list[Job] = []
        seen_urls: set[str] = set()
        companies_checked = 0

        for company in self.companies:
            name = company.get("Company Name", "")
            domain = company.get("Domain", "")
            # Careers URL is optional — auto-discovered if missing
            careers_url = (company.get("Careers Page URL") or "").strip()
            slug = domain.split(".")[0].lower() if domain else ""

            logger.info(f"Scraping: {name}")
            companies_checked += 1

            # Greenhouse API (tries domain slug as board slug)
            if slug:
                self._add_jobs(
                    scrape_greenhouse(name, slug, self.target_titles),
                    all_jobs, seen_urls,
                )
                time.sleep(0.3)

            # Lever API (tries domain slug as board slug)
            if slug:
                self._add_jobs(
                    scrape_lever(name, slug, self.target_titles),
                    all_jobs, seen_urls,
                )
                time.sleep(0.3)

            # Company-direct Playwright scrape
            # If no URL in sheet, auto-discover via common patterns
            if not careers_url and domain:
                careers_url = discover_careers_url(domain) or ""
                if careers_url:
                    logger.debug(f"Auto-discovered careers URL for {name}: {careers_url}")

            if careers_url:
                self._add_jobs(
                    scrape_company_direct(name, careers_url, self.target_titles),
                    all_jobs, seen_urls,
                )
                time.sleep(1.0)

        logger.info(f"Discovery complete: {len(all_jobs)} jobs from {companies_checked} companies")
        return all_jobs, companies_checked
