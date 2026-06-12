import time
import logging

from models.job import Job
from tools.scrapers.greenhouse import scrape_greenhouse
from tools.scrapers.lever import scrape_lever
from tools.scrapers.ashby import scrape_ashby
from tools.scrapers.company_direct import scrape_company_direct
from tools.scrapers.career_url_discovery import discover_careers_url

logger = logging.getLogger(__name__)


class DiscoveryCrew:
    def __init__(self, companies: list[dict], target_titles: list[str]):
        self.companies = companies
        self.target_titles = target_titles

    def _add_jobs(self, new_jobs: list[Job], all_jobs: list[Job], seen_urls: set[str]) -> int:
        added = 0
        for job in new_jobs:
            if job.url and job.url not in seen_urls:
                seen_urls.add(job.url)
                all_jobs.append(job)
                added += 1
        return added

    def run(self) -> tuple[list[Job], int]:
        """Returns (jobs, companies_checked)."""
        all_jobs: list[Job] = []
        seen_urls: set[str] = set()
        companies_checked = 0

        for company in self.companies:
            name = company.get("Company Name", "")
            domain = company.get("Domain", "")
            careers_url = (company.get("Careers Page URL") or "").strip()
            slug = domain.split(".")[0].lower() if domain else ""

            logger.info(f"Scraping: {name}")
            companies_checked += 1
            api_hits = 0

            # Greenhouse API
            if slug:
                api_hits += self._add_jobs(
                    scrape_greenhouse(name, slug, self.target_titles),
                    all_jobs, seen_urls,
                )
                time.sleep(0.3)

            # Lever API
            if slug:
                api_hits += self._add_jobs(
                    scrape_lever(name, slug, self.target_titles),
                    all_jobs, seen_urls,
                )
                time.sleep(0.3)

            # Ashby API
            if slug:
                api_hits += self._add_jobs(
                    scrape_ashby(name, slug, self.target_titles),
                    all_jobs, seen_urls,
                )
                time.sleep(0.3)

            # Skip Playwright if APIs already found jobs — avoids 30s timeouts on
            # enterprise portals (Amazon, IBM, Oracle, etc.) that block headless browsers
            if api_hits > 0:
                logger.debug(f"Skipping Playwright for {name} — {api_hits} jobs found via API")
                continue

            # Company-direct Playwright scrape:
            # 1. Use sheet URL if provided
            # 2. Try fast HEAD-request patterns
            # 3. Crawl homepage footer/nav (inside scrape_company_direct)
            if not careers_url and domain:
                careers_url = discover_careers_url(domain) or ""
                if careers_url:
                    logger.debug(f"HEAD-discovered careers URL for {name}: {careers_url}")

            self._add_jobs(
                scrape_company_direct(name, careers_url, self.target_titles, domain=domain),
                all_jobs, seen_urls,
            )
            time.sleep(1.0)

        logger.info(f"Discovery complete: {len(all_jobs)} jobs from {companies_checked} companies")
        return all_jobs, companies_checked
