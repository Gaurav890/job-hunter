import logging

from models.job import Job
from tools.scoring import score_job
from tools.visa_check import check_visa_tier1, apply_target_list_sponsorship

logger = logging.getLogger(__name__)


class EnrichmentCrew:
    def __init__(self, target_titles: list[str]):
        self.target_titles = target_titles

    def run(self, jobs: list[Job]) -> list[Job]:
        """Visa-check, score, filter. Returns jobs with score >= 30, sorted desc."""
        enriched: list[Job] = []

        for job in jobs:
            job = check_visa_tier1(job)
            if job.sponsorship_status == "No Sponsorship":
                continue  # hard filter — never surface

            job = apply_target_list_sponsorship(job)
            job = score_job(job, self.target_titles)

            if job.score >= 30:  # drop ⚪ Hold tier
                enriched.append(job)

        enriched.sort(key=lambda j: j.score, reverse=True)
        logger.info(f"Enrichment complete: {len(enriched)} jobs kept after filtering")
        return enriched
