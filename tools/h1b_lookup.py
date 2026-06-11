"""
H1B Tier 2 sponsorship lookup.

Queries h1bdata.info and myvisajobs.com to check whether a company has filed
H1B petitions in recent years. Results are cached in-memory for the duration
of a run so the same company is never queried twice per run.
"""

import logging
import re
import time
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _normalize(company_name: str) -> str:
    """Strip legal suffixes and special chars for cleaner lookups."""
    name = company_name.lower()
    for suffix in [" inc", " llc", " corp", " ltd", " co.", "/ aws", "/ tiktok"]:
        name = name.replace(suffix, "")
    name = re.sub(r"[^\w\s]", " ", name).strip()
    return name


def _check_h1bdata(company_name: str) -> bool | None:
    """Returns True if company has rows in h1bdata.info, None on error."""
    query = requests.utils.quote(company_name)
    url = f"https://h1bdata.info/index.php?em={query}&job=&city=&year=All+Years"
    try:
        resp = requests.get(url, timeout=12, headers=HEADERS)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        # h1bdata renders results in a <table> with id="h1bTable"
        table = soup.find("table", {"id": "h1bTable"})
        if table:
            rows = table.find_all("tr")
            return len(rows) > 1  # header + at least one data row
        return False
    except Exception as e:
        logger.debug(f"h1bdata error [{company_name}]: {e}")
        return None


def _check_myvisajobs(company_name: str) -> bool | None:
    """Returns True if company appears in myvisajobs H1B search results."""
    query = requests.utils.quote(company_name)
    url = f"https://www.myvisajobs.com/Search/?kw={query}&pt=H1B"
    try:
        resp = requests.get(url, timeout=12, headers=HEADERS)
        if resp.status_code != 200:
            return None
        return company_name.lower() in resp.text.lower()
    except Exception as e:
        logger.debug(f"myvisajobs error [{company_name}]: {e}")
        return None


@lru_cache(maxsize=500)
def lookup_h1b_history(company_name: str) -> bool:
    """
    Returns True if the company has H1B filing history.
    Tries h1bdata.info first, falls back to myvisajobs.com.
    Results are cached in-memory for the duration of the process.
    """
    normalized = _normalize(company_name)

    result = _check_h1bdata(normalized)
    time.sleep(0.5)
    if result is True:
        return True

    result = _check_myvisajobs(normalized)
    time.sleep(0.5)
    if result is True:
        return True

    return False
