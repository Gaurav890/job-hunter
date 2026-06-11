from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    company: str
    title: str
    location: str
    url: str
    source: str

    salary: str = "Unknown"
    sponsorship_status: str = "Unknown"   # Confirmed / Likely / Unknown / No Sponsorship
    sponsorship_source: str = ""          # Confirmed in Posting / H1B History / ""
    posted_date: str = ""
    date_found: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    score: int = 0
    priority: str = "⚪"

    linkedin_contacts: str = ""
    outreach_draft: str = ""

    status: str = "New"
    application_date: str = ""
    notes: str = ""

    # Internal — not written to sheet
    description: str = ""
    is_on_target_list: bool = False
    is_remote: bool = False

    def to_sheet_row(self) -> list:
        return [
            self.date_found,
            self.priority,
            self.score,
            self.company,
            self.title,
            self.location,
            self.salary,
            self.sponsorship_status,
            self.posted_date,
            self.url,
            self.source,
            self.status,
            self.application_date,
            self.notes,
            self.linkedin_contacts,
            self.outreach_draft,
        ]
