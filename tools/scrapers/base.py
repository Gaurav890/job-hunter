import re
from urllib.parse import urlparse


def title_match_score(job_title: str, target_titles: list[str]) -> tuple[bool, bool]:
    """Returns (is_exact_match, is_close_match). Close = 2+ keyword overlap."""
    STOPWORDS = {"the", "a", "an", "and", "or", "of", "in", "at", "for", "to", "with"}
    job_lower = job_title.lower().strip()

    for title in target_titles:
        if title.lower() == job_lower:
            return True, False

    job_words = set(re.findall(r'\b\w+\b', job_lower)) - STOPWORDS
    for title in target_titles:
        title_words = set(re.findall(r'\b\w+\b', title.lower())) - STOPWORDS
        if len(job_words & title_words) >= 2:
            return False, True

    return False, False


NON_US_PATTERNS = [
    r'\buk\b', r'united kingdom', r'\bcanada\b', r'\bindia\b',
    r'\beurope\b', r'\bgermany\b', r'\bfrance\b', r'\baustralia\b',
    r'\bsingapore\b', r'\bjapan\b', r'\bbrazil\b', r'\bmexico\b',
    r'outside (the )?us', r'non.?us', r'\bapac\b', r'\bemea\b',
]


def is_us_location(location: str) -> bool:
    if not location:
        return True  # assume US if unspecified
    return not any(re.search(p, location.lower()) for p in NON_US_PATTERNS)


def make_absolute_url(href: str, base_url: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"
    return ""
