"""
Smoke test — verifies all external connections before the first scheduled run.
Reads from the sheet and Supabase, runs one scraper, scores a dummy job.
Does NOT write anything to the sheet or Supabase.

    python3 test_run.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


def check(label: str, fn):
    try:
        result = fn()
        print(f"  ✓ {label}")
        return result
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        return None


def test_sheets():
    from tools.sheets import SheetsClient
    s = SheetsClient()
    companies = s.get_companies()
    titles = s.get_target_titles()
    print(f"    → {len(companies)} companies, {len(titles)} titles loaded")
    return companies, titles


def test_supabase():
    from tools.supabase_store import SupabaseStore
    store = SupabaseStore()
    # Probe: check a URL that definitely doesn't exist
    store.job_exists("https://smoke-test-probe.invalid")
    return store


def test_greenhouse(companies, titles):
    from tools.scrapers.greenhouse import scrape_greenhouse
    # Pick a company whose slug is likely on Greenhouse
    candidates = [c for c in companies if c.get("Domain")]
    company = next((c for c in candidates if c["Company Name"] in ("Stripe", "Databricks", "Glean")), candidates[0])
    name = company["Company Name"]
    slug = company["Domain"].split(".")[0]
    jobs = scrape_greenhouse(name, slug, titles)
    print(f"    → {len(jobs)} matching jobs found for {name}")
    return jobs


def test_lever(companies, titles):
    from tools.scrapers.lever import scrape_lever
    candidates = [c for c in companies if c.get("Domain")]
    company = next((c for c in candidates if c["Company Name"] in ("Notion", "Linear", "Airtable")), candidates[0])
    name = company["Company Name"]
    slug = company["Domain"].split(".")[0]
    jobs = scrape_lever(name, slug, titles)
    print(f"    → {len(jobs)} matching jobs found for {name}")


def test_scoring(titles):
    from models.job import Job
    from tools.scoring import score_job
    job = Job(
        company="OpenAI", title="AI Product Manager",
        location="San Francisco, CA (Remote)",
        url="https://example.com/job/1", source="test",
        is_on_target_list=True, sponsorship_status="Likely",
    )
    job = score_job(job, titles)
    print(f"    → score={job.score}, priority={job.priority}")


def test_visa_check():
    from models.job import Job
    from tools.visa_check import check_visa_tier1
    job = Job(company="Test Co", title="AI PM", location="Remote",
              url="https://x.com", source="test",
              description="We will sponsor H1B visas for qualified candidates.")
    job = check_visa_tier1(job)
    assert job.sponsorship_status == "Confirmed", f"Expected Confirmed, got {job.sponsorship_status}"
    print(f"    → sponsorship correctly detected: {job.sponsorship_status}")


def test_anthropic():
    from agents.linkedin import generate_outreach_draft
    from models.job import Job
    job = Job(company="Anthropic", title="AI Product Manager",
              location="San Francisco, CA", url="https://x.com", source="test",
              linkedin_contacts="No connection — cold outreach")
    draft = generate_outreach_draft(job)
    preview = draft[:80].replace("\n", " ")
    print(f"    → draft: \"{preview}...\"")


if __name__ == "__main__":
    print("\nJobHunter smoke test\n" + "─" * 40)

    print("\n[1] Google Sheets")
    result = check("Connect + load config", test_sheets)
    companies, titles = result if result else ([], [])

    print("\n[2] Supabase")
    check("Connect + probe", test_supabase)

    if companies and titles:
        print("\n[3] Scrapers")
        check("Greenhouse API", lambda: test_greenhouse(companies, titles))
        check("Lever API", lambda: test_lever(companies, titles))

        print("\n[4] Scoring + visa check")
        check("Scoring engine", lambda: test_scoring(titles))
        check("Visa Tier 1 keyword scan", test_visa_check)

    print("\n[5] Claude API (outreach draft)")
    check("Anthropic API", test_anthropic)

    print("\n" + "─" * 40)
    print("Done. Fix any ✗ failures before your first scheduled run.\n")
