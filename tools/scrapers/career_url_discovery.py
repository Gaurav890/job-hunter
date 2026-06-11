"""
Auto-discovers the careers page URL for a company by trying common patterns
with fast HEAD requests. Falls back gracefully if nothing resolves.
"""

import logging
import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

PATTERNS = [
    "https://{domain}/careers",
    "https://{domain}/jobs",
    "https://careers.{domain}",
    "https://jobs.{domain}",
    "https://{domain}/about/careers",
    "https://{domain}/company/careers",
    "https://{domain}/en-us/careers",
    "https://{domain}/careers/jobs",
    "https://{domain}/work-with-us",
]


def discover_careers_url(domain: str) -> str | None:
    """
    Tries common career page URL patterns and returns the first that resolves.
    Uses HEAD requests (fast, no body download).
    Returns None if nothing resolves.
    """
    for pattern in PATTERNS:
        url = pattern.format(domain=domain)
        try:
            resp = requests.head(
                url, timeout=5, allow_redirects=True, headers=HEADERS
            )
            if resp.status_code == 200:
                logger.debug(f"Discovered careers URL for {domain}: {url}")
                return url
        except Exception:
            continue
    return None
