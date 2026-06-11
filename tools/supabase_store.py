"""
Supabase dedup store and run log.

Required schema (run once in Supabase SQL editor):

    create table jobs (
        id uuid primary key default gen_random_uuid(),
        url text unique not null,
        company text not null,
        title text not null,
        location text not null,
        status text not null default 'New',
        created_at timestamptz default now()
    );

    create table run_logs (
        id uuid primary key default gen_random_uuid(),
        run_timestamp timestamptz default now(),
        jobs_found int,
        new_jobs_added int,
        companies_checked int,
        errors text,
        duration_seconds int
    );
"""

import logging
from datetime import datetime

from supabase import create_client, Client

from config.settings import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)


class SupabaseStore:
    def __init__(self):
        self._db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def job_exists(self, url: str) -> bool:
        result = self._db.table("jobs").select("id").eq("url", url).execute()
        return len(result.data) > 0

    def is_terminal(self, url: str) -> bool:
        """Returns True if job was previously Rejected or Offer — skip permanently."""
        result = (
            self._db.table("jobs")
            .select("status")
            .eq("url", url)
            .in_("status", ["Rejected", "Offer"])
            .execute()
        )
        return len(result.data) > 0

    def add_job(self, url: str, company: str, title: str, location: str) -> None:
        try:
            self._db.table("jobs").insert({
                "url": url,
                "company": company,
                "title": title,
                "location": location,
                "status": "New",
            }).execute()
        except Exception as e:
            logger.warning(f"Supabase insert failed for {url}: {e}")

    def log_run(self, jobs_found: int, new_jobs: int, companies_checked: int,
                errors: str, duration_seconds: int) -> None:
        try:
            self._db.table("run_logs").insert({
                "run_timestamp": datetime.utcnow().isoformat(),
                "jobs_found": jobs_found,
                "new_jobs_added": new_jobs,
                "companies_checked": companies_checked,
                "errors": errors,
                "duration_seconds": duration_seconds,
            }).execute()
        except Exception as e:
            logger.warning(f"Supabase run log failed: {e}")
