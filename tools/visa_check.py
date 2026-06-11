import logging

from models.job import Job
from config.settings import SPONSORSHIP_INCLUDE_KEYWORDS, SPONSORSHIP_EXCLUDE_KEYWORDS

logger = logging.getLogger(__name__)


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


def check_visa_tier2(job: Job) -> Job:
    """
    Queries H1B filing databases for companies not on the target list
    and where Tier 1 found no explicit sponsorship language.
    Only runs when sponsorship is still undecided AND job is not from target list.
    """
    if job.sponsorship_status in ("Confirmed", "No Sponsorship"):
        return job
    if job.is_on_target_list:
        return job  # handled by apply_target_list_sponsorship

    try:
        from tools.h1b_lookup import lookup_h1b_history
        has_history = lookup_h1b_history(job.company)
        if has_history:
            job.sponsorship_status = "Likely"
            job.sponsorship_source = "H1B History"
            logger.info(f"Tier 2 confirmed H1B history: {job.company}")
        else:
            job.sponsorship_status = "Unknown"
    except Exception as e:
        logger.warning(f"Tier 2 lookup failed for {job.company}: {e}")
        job.sponsorship_status = "Unknown"

    return job


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
