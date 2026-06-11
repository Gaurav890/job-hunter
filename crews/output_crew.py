import logging
import time

from models.job import Job
from tools.sheets import SheetsClient
from tools.supabase_store import SupabaseStore

logger = logging.getLogger(__name__)


class OutputCrew:
    def __init__(self):
        self.sheets = SheetsClient()
        self.store = SupabaseStore()

    def run(
        self,
        jobs: list[Job],
        companies_checked: int,
        run_start: float,
        errors: list[str],
    ) -> int:
        """Dedup → write sheet → log run. Returns count of new jobs written."""
        new_jobs: list[Job] = []
        for job in jobs:
            if not job.url:
                continue
            if self.store.is_terminal(job.url):
                continue  # permanently skip Rejected / Offer
            if self.store.job_exists(job.url):
                continue
            new_jobs.append(job)

        written = 0
        if new_jobs:
            written = self.sheets.write_jobs(new_jobs)
            for job in new_jobs:
                self.store.add_job(job.url, job.company, job.title, job.location)

        duration_sec = int(time.time() - run_start)
        duration_min = duration_sec / 60
        error_str = "; ".join(errors) if errors else ""

        self.sheets.log_run(
            jobs_found=len(jobs),
            new_jobs=written,
            companies_checked=companies_checked,
            errors=error_str,
            duration_min=duration_min,
        )
        self.store.log_run(
            jobs_found=len(jobs),
            new_jobs=written,
            companies_checked=companies_checked,
            errors=error_str,
            duration_seconds=duration_sec,
        )

        logger.info(f"Output complete: {written} new jobs written to sheet")
        return written
