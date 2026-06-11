import time
import logging

from models.job import Job
from tools.scrapers.greenhouse import scrape_greenhouse
from tools.scrapers.lever import scrape_lever
from tools.scrapers.company_direct import scrape_company_direct

logger = logging.getLogger(__name__)


class DiscoveryCrew:
    def __init__(self, companies: list[dict], target_titles: list[str]):
        self.companies = companies
        self.target_titles = target_titles

    def run(self) -> tuple[list[Job], int]:
        """Returns (jobs, companies_checked)."""
        all_jobs: list[Job] = []
        seen_urls: set[str] = set()
        companies_checked = 0

        for company in self.companies:
            name = company.get("Company Name", "")
            domain = company.get("Domain", "")
            careers_url = company.get("Careers Page URL", "")
            slug = domain.split(".")[0].lower() if domain else ""

            logger.info(f"Scraping: {name}")
            companies_checked += 1

            if slug:
                for job in scrape_greenhouse(name, slug, self.target_titles):
                    if job.url and job.url not in seen_urls:
                        seen_urls.add(job.url)
                        all_jobs.append(job)
                time.sleep(0.3)

                for job in scrape_lever(name, slug, self.target_titles):
                    if job.url and job.url not in seen_urls:
                        seen_urls.add(job.url)
                        all_jobs.append(job)
                time.sleep(0.3)

            if careers_url:
                for job in scrape_company_direct(name, careers_url, self.target_titles):
                    if job.url and job.url not in seen_urls:
                        seen_urls.add(job.url)
                        all_jobs.append(job)
                time.sleep(1.0)

        logger.info(f"Discovery complete: {len(all_jobs)} jobs from {companies_checked} companies")
        return all_jobs, companies_checked
