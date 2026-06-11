import logging

import anthropic

from models.job import Job
from config.settings import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

GAURAV_BACKGROUND = (
    "Built Followloop (AI-powered social media growth tool); "
    "won Cal Hacks (UC Berkeley's flagship hackathon); "
    "deployed AI solutions at FleetPanda (fleet management SaaS) — "
    "strong background bridging AI product strategy with enterprise deployment."
)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _fallback_draft(job: Job) -> str:
    return (
        f"Hi, I noticed {job.company} is hiring for {job.title}. "
        f"My background deploying AI products (Followloop, Cal Hacks win, FleetPanda) "
        f"aligns well with this role. Would love to learn more about the team — "
        f"open to a quick chat?"
    )


def generate_outreach_draft(job: Job) -> str:
    contact_line = job.linkedin_contacts or "no specific contact found"

    prompt = f"""Write a LinkedIn outreach message for Gaurav Chaulagain. Max 4 lines. No preamble — just the message.

Gaurav's background: {GAURAV_BACKGROUND}

Job: {job.title} at {job.company} ({job.location})
Contact info: {contact_line}

Format: Hey [Name/Team], noticed {job.company} is hiring for {job.title}. [One sentence tying Gaurav's background to this specific role/company]. Would love to learn more. Open to a quick chat?

Rules: conversational, specific to this company/role, not generic."""

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Outreach draft failed for {job.company}: {e}")
        return _fallback_draft(job)
