import logging
import time
from datetime import datetime

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import SCHEDULE_HOURS_PT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

PT = pytz.timezone("America/Los_Angeles")


def run_job_hunt():
    run_start = time.time()
    errors: list[str] = []
    companies_checked = 0
    jobs = []

    logger.info(f"=== Run starting {datetime.now(PT).strftime('%Y-%m-%d %H:%M %Z')} ===")

    try:
        from tools.sheets import SheetsClient
        sheets = SheetsClient()
        companies = sheets.get_companies()
        target_titles = sheets.get_target_titles()
        logger.info(f"Loaded {len(companies)} companies, {len(target_titles)} titles")
    except Exception as e:
        logger.error(f"Failed to load config from sheet: {e}", exc_info=True)
        return

    try:
        from crews.discovery_crew import DiscoveryCrew
        jobs, companies_checked = DiscoveryCrew(companies, target_titles).run()
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        errors.append(f"discovery: {e}")

    try:
        from crews.enrichment_crew import EnrichmentCrew
        jobs = EnrichmentCrew(target_titles).run(jobs)
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        errors.append(f"enrichment: {e}")

    try:
        from crews.linkedin_crew import LinkedInCrew
        jobs = LinkedInCrew(companies).run(jobs)
    except Exception as e:
        logger.error(f"LinkedIn crew failed: {e}", exc_info=True)
        errors.append(f"linkedin: {e}")

    try:
        from crews.output_crew import OutputCrew
        new_count = OutputCrew().run(jobs, companies_checked, run_start, errors)
        logger.info(f"Run complete — {new_count} new jobs added to sheet")
    except Exception as e:
        logger.error(f"Output failed: {e}", exc_info=True)

    logger.info(f"=== Run finished in {(time.time() - run_start) / 60:.1f} min ===")


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=PT)

    for hour in SCHEDULE_HOURS_PT:
        scheduler.add_job(
            run_job_hunt,
            CronTrigger(hour=hour, minute=0, timezone=PT),
            id=f"job_hunt_{hour}h",
        )

    logger.info(f"Scheduler started — runs at {SCHEDULE_HOURS_PT[0]}AM and {SCHEDULE_HOURS_PT[1] - 12}PM PT daily")
    scheduler.start()
