import re
from datetime import datetime, timezone

from models.job import Job
from config.settings import SCORE_WEIGHTS, PRIORITY_TIERS, SALARY_MINIMUM


def _extract_salary(text: str) -> tuple[bool, str]:
    """Returns (meets_minimum, display_str)."""
    if not text:
        return False, "Unknown"

    matches = re.finditer(r'\$[\d,]+\.?\d*[kK]?|\b[\d,]+\.?\d*[kK]\b', text)
    amounts = []
    for m in matches:
        raw = m.group().replace("$", "").replace(",", "").strip()
        is_k = raw.lower().endswith("k")
        raw = raw.lower().rstrip("k")
        try:
            val = float(raw) * (1000 if is_k else 1)
            if 30_000 <= val <= 1_000_000:
                amounts.append(int(val))
        except ValueError:
            continue

    if not amounts:
        return False, "Unknown"
    best = max(amounts)
    return best >= SALARY_MINIMUM, f"${best:,}"


def _hours_since(date_str: str) -> float:
    if not date_str:
        return 9999
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return 9999


def score_job(job: Job, target_titles: list[str]) -> Job:
    score = 0

    if job.is_on_target_list:
        score += SCORE_WEIGHTS["on_target_list"]

    title_lower = job.title.lower()
    exact = any(t.lower() == title_lower for t in target_titles)
    if exact:
        score += SCORE_WEIGHTS["exact_title_match"]
    else:
        job_words = set(re.findall(r'\b\w+\b', title_lower))
        close = any(
            len(job_words & set(re.findall(r'\b\w+\b', t.lower()))) >= 2
            for t in target_titles
        )
        if close:
            score += SCORE_WEIGHTS["close_title_match"]

    salary_text = (job.description or "") + " " + (job.salary or "")
    salary_ok, salary_str = _extract_salary(salary_text)
    if salary_ok:
        score += SCORE_WEIGHTS["salary_confirmed"]
    if salary_str != "Unknown":
        job.salary = salary_str

    if job.sponsorship_status == "Confirmed":
        if job.sponsorship_source == "Confirmed in Posting":
            score += SCORE_WEIGHTS["sponsorship_confirmed_posting"]
        else:
            score += SCORE_WEIGHTS["sponsorship_confirmed_h1b"]
    elif job.sponsorship_status == "Likely":
        score += SCORE_WEIGHTS["sponsorship_confirmed_h1b"]

    hours = _hours_since(job.posted_date)
    if hours <= 24:
        score += SCORE_WEIGHTS["posted_24h"]
    elif hours <= 72:
        score += SCORE_WEIGHTS["posted_72h"]

    if "remote" in job.location.lower() or "remote" in job.title.lower():
        score += SCORE_WEIGHTS["is_remote"]
        job.is_remote = True

    job.score = score
    for min_score, emoji in PRIORITY_TIERS:
        if score >= min_score:
            job.priority = emoji
            break

    return job
