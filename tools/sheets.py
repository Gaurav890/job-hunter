import json
import logging
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from config.settings import (
    GOOGLE_SHEET_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
    TAB_JOB_TRACKER,
    TAB_COMPANY_LIST,
    TAB_TITLE_CONFIG,
    TAB_RUN_LOG,
    JOB_TRACKER_HEADERS,
)
from models.job import Job

logger = logging.getLogger(__name__)

class SheetsClient:
    def __init__(self):
        creds = Credentials(
            token=None,
            refresh_token=GOOGLE_REFRESH_TOKEN,
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token",
        )
        creds.refresh(Request())
        self._client = gspread.authorize(creds)
        self._sheet = self._client.open_by_key(GOOGLE_SHEET_ID)

    def _tab(self, name: str) -> gspread.Worksheet:
        return self._sheet.worksheet(name)

    # ── Read helpers ──────────────────────────────────────────────────────────

    def get_companies(self) -> list[dict]:
        """Returns all rows from Company List tab as list of dicts."""
        ws = self._tab(TAB_COMPANY_LIST)
        return ws.get_all_records()

    def get_target_titles(self) -> list[str]:
        """Returns all titles from Role Title Config tab."""
        ws = self._tab(TAB_TITLE_CONFIG)
        values = ws.col_values(1)
        return [v for v in values[1:] if v]  # skip header row

    def get_existing_urls(self) -> set[str]:
        """Returns all job URLs already in the tracker (for dedup)."""
        ws = self._tab(TAB_JOB_TRACKER)
        url_col_idx = JOB_TRACKER_HEADERS.index("Job URL") + 1
        values = ws.col_values(url_col_idx)
        return set(values[1:])  # skip header

    def get_terminal_urls(self) -> set[str]:
        """Returns URLs for jobs in terminal states (Rejected, Offer) — never re-surface."""
        ws = self._tab(TAB_JOB_TRACKER)
        records = ws.get_all_records()
        return {r["Job URL"] for r in records if r.get("Status") in ("Rejected", "Offer")}

    # ── Write helpers ─────────────────────────────────────────────────────────

    def write_jobs(self, jobs: list[Job]) -> int:
        """Appends jobs to Job Tracker tab. Returns count written."""
        if not jobs:
            return 0
        ws = self._tab(TAB_JOB_TRACKER)
        rows = [job.to_sheet_row() for job in jobs]
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info(f"Wrote {len(rows)} jobs to sheet")
        return len(rows)

    def update_company_last_checked(self, company_name: str) -> None:
        ws = self._tab(TAB_COMPANY_LIST)
        records = ws.get_all_records()
        for i, row in enumerate(records, start=2):  # row 1 is header
            if row.get("Company Name") == company_name:
                last_checked_col = 6  # column F
                ws.update_cell(i, last_checked_col, datetime.now().strftime("%Y-%m-%d %H:%M"))
                return

    def log_run(self, jobs_found: int, new_jobs: int, companies_checked: int,
                errors: str, duration_min: float) -> None:
        ws = self._tab(TAB_RUN_LOG)
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            jobs_found,
            new_jobs,
            companies_checked,
            errors,
            round(duration_min, 1),
        ], value_input_option="USER_ENTERED")
