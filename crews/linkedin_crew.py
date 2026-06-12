import logging
import time

from models.job import Job

logger = logging.getLogger(__name__)

# Only run LinkedIn lookups on Priority 1+2 — avoids rate limits and keeps runtime sane.
# Outreach drafts are generated for all jobs (fast Claude API call).
LINKEDIN_PRIORITY_THRESHOLD = "🟡"  # 🔴 and 🟡


class LinkedInCrew:
    def __init__(self, companies: list[dict]):
        self._domain_map = {c["Company Name"]: c.get("Domain", "") for c in companies}

    def run(self, jobs: list[Job]) -> list[Job]:
        from agents.linkedin import generate_outreach_draft

        p1_p2 = [j for j in jobs if j.priority in ("🔴", "🟡")]
        p3 = [j for j in jobs if j.priority not in ("🔴", "🟡")]

        logger.info(
            f"LinkedIn crew: {len(p1_p2)} P1/P2 jobs get full lookup, "
            f"{len(p3)} P3 jobs get draft only"
        )

        # Generate outreach drafts for all jobs (LinkedIn lookup skipped —
        # headless Playwright is blocked by LinkedIn's bot detection)
        for job in p1_p2 + p3:
            job.linkedin_contacts = "Manual lookup — visit linkedin.com/company/{}/people/".format(
                self._domain_map.get(job.company, job.company.lower().replace(" ", "-")).split(".")[0]
            )
            try:
                job.outreach_draft = generate_outreach_draft(job)
            except Exception as e:
                logger.warning(f"Draft error [{job.company}]: {e}")

        logger.info(f"LinkedIn crew complete: {len(jobs)} jobs enriched")
        return jobs
