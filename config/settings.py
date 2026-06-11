import os
import json
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

LINKEDIN_COOKIE_LI_AT = os.getenv("LINKEDIN_COOKIE_LI_AT")

SALARY_MINIMUM = 150_000

SCHEDULE_HOURS_PT = [6, 13]  # 6AM and 1PM Pacific

TARGET_TITLES = [
    "AI Product Manager",
    "Technical Product Manager",
    "Forward Deployed Engineer",
    "Forward Deployed Product Manager",
    "AI Solutions Engineer",
    "AI Solutions Architect",
    "Agent Strategist",
    "Enterprise AI Strategist",
    "AI Implementation Manager",
    "Solutions Engineer (AI)",
    "Customer Success Engineer (AI)",
    "AI Deployment Strategist",
]

SCORE_WEIGHTS = {
    "on_target_list": 30,
    "exact_title_match": 20,
    "close_title_match": 10,
    "salary_confirmed": 15,
    "sponsorship_confirmed_posting": 15,
    "sponsorship_confirmed_h1b": 10,
    "posted_24h": 10,
    "posted_72h": 5,
    "is_remote": 5,
}

# (min_score_inclusive, emoji_label)
PRIORITY_TIERS = [
    (70, "🔴"),
    (50, "🟡"),
    (30, "🟢"),
    (0,  "⚪"),
]

SPONSORSHIP_INCLUDE_KEYWORDS = [
    "will sponsor", "visa sponsorship available", "sponsorship provided",
    "h1b sponsor", "open to sponsoring", "we sponsor",
]
SPONSORSHIP_EXCLUDE_KEYWORDS = [
    "no sponsorship", "must be authorized to work",
    "we do not sponsor", "us citizen or permanent resident only",
    "cannot sponsor", "not able to sponsor",
]

TAB_JOB_TRACKER   = "Job Tracker"
TAB_COMPANY_LIST  = "Company List"
TAB_TITLE_CONFIG  = "Role Title Config"
TAB_RUN_LOG       = "Run Log"

JOB_TRACKER_HEADERS = [
    "Date Found", "Priority", "Score", "Company", "Role Title",
    "Location", "Salary", "Sponsorship Status", "Posted Date",
    "Job URL", "Source", "Status", "Application Date",
    "Notes", "LinkedIn Contacts", "Outreach Draft",
]

COMPANY_LIST_HEADERS = [
    "Company Name", "Domain", "Category", "Careers Page URL",
    "H1B History", "Last Checked", "Notes",
]

RUN_LOG_HEADERS = [
    "Run Timestamp", "Jobs Found", "New Jobs Added",
    "Companies Checked", "Errors", "Duration (min)",
]
