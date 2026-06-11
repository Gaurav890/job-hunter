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
    start = time.time()
    logger.info(f"=== Job hunt run starting at {datetime.now(PT).strftime('%Y-%m-%d %H:%M %Z')} ===")

    try:
        # Phase 2: discovery crew
        # from crews.discovery_crew import DiscoveryCrew
        # jobs = DiscoveryCrew().run()

        # Phase 3: enrichment crew (scoring + visa)
        # from crews.enrichment_crew import EnrichmentCrew
        # jobs = EnrichmentCrew().run(jobs)

        # Phase 5: LinkedIn crew
        # from crews.linkedin_crew import LinkedInCrew
        # jobs = LinkedInCrew().run(jobs)

        # Phase 3+: output crew (dedup + sheet write + run log)
        # from crews.output_crew import OutputCrew
        # OutputCrew().run(jobs)

        logger.info("Scaffold run complete — crews will be wired in Phase 2+")

    except Exception as e:
        logger.error(f"Run failed: {e}", exc_info=True)

    duration_min = (time.time() - start) / 60
    logger.info(f"=== Run finished in {duration_min:.1f} min ===")


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=PT)

    for hour in SCHEDULE_HOURS_PT:
        scheduler.add_job(
            run_job_hunt,
            CronTrigger(hour=hour, minute=0, timezone=PT),
            id=f"job_hunt_{hour}h",
        )

    logger.info(f"Scheduler started — runs at {SCHEDULE_HOURS_PT[0]}AM and {SCHEDULE_HOURS_PT[1]-12}PM PT daily")
    scheduler.start()
