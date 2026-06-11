from models.job import Job
from config.settings import SPONSORSHIP_INCLUDE_KEYWORDS, SPONSORSHIP_EXCLUDE_KEYWORDS


def check_visa_tier1(job: Job) -> Job:
    """Scans job description for explicit sponsorship language."""
    text = ((job.description or "") + " " + (job.title or "")).lower()

    if any(kw in text for kw in SPONSORSHIP_EXCLUDE_KEYWORDS):
        job.sponsorship_status = "No Sponsorship"
        return job

    if any(kw in text for kw in SPONSORSHIP_INCLUDE_KEYWORDS):
        job.sponsorship_status = "Confirmed"
        job.sponsorship_source = "Confirmed in Posting"
        return job

    return job  # undecided — Tier 2 / target list check next


def apply_target_list_sponsorship(job: Job) -> Job:
    """All 139 companies on the target list are confirmed H1B sponsors."""
    if job.sponsorship_status in ("Confirmed", "No Sponsorship"):
        return job
    if job.is_on_target_list:
        job.sponsorship_status = "Likely"
        job.sponsorship_source = "H1B History"
    else:
        job.sponsorship_status = "Unknown"
    return job
