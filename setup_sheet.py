"""
One-time script to initialize the Google Sheet with all 4 tabs, headers,
company list (Tab 2), and target titles (Tab 3).

Run once after creating your Google Sheet:
    python setup_sheet.py
"""

import sys

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from config.settings import (
    GOOGLE_SHEET_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
    TARGET_TITLES,
    TAB_JOB_TRACKER,
    TAB_COMPANY_LIST,
    TAB_TITLE_CONFIG,
    TAB_RUN_LOG,
    JOB_TRACKER_HEADERS,
    COMPANY_LIST_HEADERS,
    RUN_LOG_HEADERS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COMPANIES = [
    # ── Enterprise Software & Cloud ───────────────────────────────────────────
    ("Salesforce",          "salesforce.com",         "Enterprise Software & Cloud"),
    ("Microsoft",           "microsoft.com",           "Enterprise Software & Cloud"),
    ("Google",              "google.com",              "Enterprise Software & Cloud"),
    ("Amazon / AWS",        "amazon.com",              "Enterprise Software & Cloud"),
    ("IBM",                 "ibm.com",                 "Enterprise Software & Cloud"),
    ("Oracle",              "oracle.com",              "Enterprise Software & Cloud"),
    ("SAP",                 "sap.com",                 "Enterprise Software & Cloud"),
    ("ServiceNow",          "servicenow.com",          "Enterprise Software & Cloud"),
    ("Workday",             "workday.com",             "Enterprise Software & Cloud"),
    ("Snowflake",           "snowflake.com",           "Enterprise Software & Cloud"),
    ("Databricks",          "databricks.com",          "Enterprise Software & Cloud"),
    ("Palantir",            "palantir.com",            "Enterprise Software & Cloud"),
    ("UiPath",              "uipath.com",              "Enterprise Software & Cloud"),
    ("Twilio",              "twilio.com",              "Enterprise Software & Cloud"),
    ("Zendesk",             "zendesk.com",             "Enterprise Software & Cloud"),
    ("HubSpot",             "hubspot.com",             "Enterprise Software & Cloud"),
    ("Atlassian",           "atlassian.com",           "Enterprise Software & Cloud"),
    ("Box",                 "box.com",                 "Enterprise Software & Cloud"),
    ("DocuSign",            "docusign.com",            "Enterprise Software & Cloud"),
    ("Veeva Systems",       "veeva.com",               "Enterprise Software & Cloud"),
    ("Sprinklr",            "sprinklr.com",            "Enterprise Software & Cloud"),
    ("Qualtrics",           "qualtrics.com",           "Enterprise Software & Cloud"),
    ("MuleSoft",            "mulesoft.com",            "Enterprise Software & Cloud"),
    ("Appian",              "appian.com",              "Enterprise Software & Cloud"),
    ("Medallia",            "medallia.com",            "Enterprise Software & Cloud"),

    # ── AI & Tech Startups ────────────────────────────────────────────────────
    ("OpenAI",              "openai.com",              "AI & Tech Startups"),
    ("Anthropic",           "anthropic.com",           "AI & Tech Startups"),
    ("Cohere",              "cohere.com",              "AI & Tech Startups"),
    ("Scale AI",            "scale.com",               "AI & Tech Startups"),
    ("Glean",               "glean.com",               "AI & Tech Startups"),
    ("Writer",              "writer.com",              "AI & Tech Startups"),
    ("Harvey AI",           "harvey.ai",               "AI & Tech Startups"),
    ("Moveworks",           "moveworks.com",           "AI & Tech Startups"),
    ("Aisera",              "aisera.com",              "AI & Tech Startups"),
    ("Observe.AI",          "observe.ai",              "AI & Tech Startups"),
    ("Cresta",              "cresta.com",              "AI & Tech Startups"),
    ("Sierra AI",           "sierra.ai",               "AI & Tech Startups"),
    ("Clay",                "clay.com",                "AI & Tech Startups"),
    ("Weights & Biases",    "wandb.ai",                "AI & Tech Startups"),
    ("Hugging Face",        "huggingface.co",          "AI & Tech Startups"),
    ("LangChain",           "langchain.com",           "AI & Tech Startups"),
    ("Runway ML",           "runwayml.com",            "AI & Tech Startups"),
    ("Pika Labs",           "pika.art",                "AI & Tech Startups"),
    ("Descript",            "descript.com",            "AI & Tech Startups"),
    ("Notion",              "notion.so",               "AI & Tech Startups"),
    ("Airtable",            "airtable.com",            "AI & Tech Startups"),
    ("Linear",              "linear.app",              "AI & Tech Startups"),
    ("C3.ai",               "c3.ai",                   "AI & Tech Startups"),
    ("Automation Anywhere", "automationanywhere.com",  "AI & Tech Startups"),
    ("Adept AI",            "adept.ai",                "AI & Tech Startups"),
    ("Inflection AI",       "inflection.ai",           "AI & Tech Startups"),
    ("Character.ai",        "character.ai",            "AI & Tech Startups"),
    ("Leena AI",            "leena.ai",                "AI & Tech Startups"),
    ("11x.ai",              "11x.ai",                  "AI & Tech Startups"),
    ("Dust",                "dust.tt",                 "AI & Tech Startups"),
    ("Loom",                "loom.com",                "AI & Tech Startups"),
    ("Jasper",              "jasper.ai",               "AI & Tech Startups"),
    ("Stability AI",        "stability.ai",            "AI & Tech Startups"),
    ("Mistral",             "mistral.ai",              "AI & Tech Startups"),
    ("Together AI",         "together.ai",             "AI & Tech Startups"),

    # ── Cybersecurity & Developer Tools ───────────────────────────────────────
    ("CrowdStrike",         "crowdstrike.com",         "Cybersecurity & Developer Tools"),
    ("Palo Alto Networks",  "paloaltonetworks.com",    "Cybersecurity & Developer Tools"),
    ("Okta",                "okta.com",                "Cybersecurity & Developer Tools"),
    ("SentinelOne",         "sentinelone.com",         "Cybersecurity & Developer Tools"),
    ("Wiz",                 "wiz.io",                  "Cybersecurity & Developer Tools"),
    ("Lacework",            "lacework.com",            "Cybersecurity & Developer Tools"),
    ("Darktrace",           "darktrace.com",           "Cybersecurity & Developer Tools"),
    ("Snyk",                "snyk.io",                 "Cybersecurity & Developer Tools"),
    ("Datadog",             "datadoghq.com",           "Cybersecurity & Developer Tools"),
    ("Splunk",              "splunk.com",              "Cybersecurity & Developer Tools"),
    ("GitHub",              "github.com",              "Cybersecurity & Developer Tools"),
    ("GitLab",              "gitlab.com",              "Cybersecurity & Developer Tools"),
    ("JFrog",               "jfrog.com",               "Cybersecurity & Developer Tools"),
    ("HashiCorp",           "hashicorp.com",           "Cybersecurity & Developer Tools"),
    ("New Relic",           "newrelic.com",            "Cybersecurity & Developer Tools"),

    # ── Semiconductors & Hardware ─────────────────────────────────────────────
    ("NVIDIA",              "nvidia.com",              "Semiconductors & Hardware"),
    ("AMD",                 "amd.com",                 "Semiconductors & Hardware"),
    ("Intel",               "intel.com",               "Semiconductors & Hardware"),
    ("Qualcomm",            "qualcomm.com",            "Semiconductors & Hardware"),
    ("Arm",                 "arm.com",                 "Semiconductors & Hardware"),
    ("Broadcom",            "broadcom.com",            "Semiconductors & Hardware"),
    ("Marvell",             "marvell.com",             "Semiconductors & Hardware"),
    ("Cerebras Systems",    "cerebras.net",            "Semiconductors & Hardware"),
    ("Groq",                "groq.com",                "Semiconductors & Hardware"),
    ("SambaNova",           "sambanova.ai",            "Semiconductors & Hardware"),
    ("d-Matrix",            "d-matrix.ai",             "Semiconductors & Hardware"),
    ("Graphcore",           "graphcore.ai",            "Semiconductors & Hardware"),

    # ── Internet & Social Media ───────────────────────────────────────────────
    ("Meta",                "meta.com",                "Internet & Social Media"),
    ("LinkedIn",            "linkedin.com",            "Internet & Social Media"),
    ("Snap",                "snap.com",                "Internet & Social Media"),
    ("Pinterest",           "pinterest.com",           "Internet & Social Media"),
    ("Reddit",              "reddit.com",              "Internet & Social Media"),
    ("Discord",             "discord.com",             "Internet & Social Media"),
    ("ByteDance / TikTok",  "bytedance.com",           "Internet & Social Media"),
    ("Quora",               "quora.com",               "Internet & Social Media"),
    ("Twitch",              "twitch.tv",               "Internet & Social Media"),
    ("X (Twitter)",         "x.com",                   "Internet & Social Media"),

    # ── Entertainment & Gaming ────────────────────────────────────────────────
    ("Netflix",             "netflix.com",             "Entertainment & Gaming"),
    ("Spotify",             "spotify.com",             "Entertainment & Gaming"),
    ("Epic Games",          "epicgames.com",           "Entertainment & Gaming"),
    ("Unity Technologies",  "unity.com",               "Entertainment & Gaming"),
    ("Electronic Arts",     "ea.com",                  "Entertainment & Gaming"),
    ("Roblox",              "roblox.com",              "Entertainment & Gaming"),
    ("Riot Games",          "riotgames.com",           "Entertainment & Gaming"),
    ("Take-Two Interactive","take2games.com",           "Entertainment & Gaming"),
    ("Disney",              "disney.com",              "Entertainment & Gaming"),
    ("Activision Blizzard", "activisionblizzard.com",  "Entertainment & Gaming"),

    # ── E-commerce & On-Demand ────────────────────────────────────────────────
    ("Shopify",             "shopify.com",             "E-commerce & On-Demand"),
    ("eBay",                "ebay.com",                "E-commerce & On-Demand"),
    ("Etsy",                "etsy.com",                "E-commerce & On-Demand"),
    ("Instacart",           "instacart.com",           "E-commerce & On-Demand"),
    ("DoorDash",            "doordash.com",            "E-commerce & On-Demand"),
    ("Airbnb",              "airbnb.com",              "E-commerce & On-Demand"),
    ("Lyft",                "lyft.com",                "E-commerce & On-Demand"),
    ("Wayfair",             "wayfair.com",             "E-commerce & On-Demand"),
    ("Chewy",               "chewy.com",               "E-commerce & On-Demand"),
    ("Expedia",             "expedia.com",             "E-commerce & On-Demand"),

    # ── Fintech & Digital Payments ────────────────────────────────────────────
    ("Stripe",              "stripe.com",              "Fintech & Digital Payments"),
    ("Block (Square)",      "block.xyz",               "Fintech & Digital Payments"),
    ("PayPal",              "paypal.com",              "Fintech & Digital Payments"),
    ("Brex",                "brex.com",                "Fintech & Digital Payments"),
    ("Plaid",               "plaid.com",               "Fintech & Digital Payments"),
    ("Affirm",              "affirm.com",              "Fintech & Digital Payments"),
    ("Robinhood",           "robinhood.com",           "Fintech & Digital Payments"),
    ("Coinbase",            "coinbase.com",            "Fintech & Digital Payments"),
    ("Ramp",                "ramp.com",                "Fintech & Digital Payments"),
    ("Mercury",             "mercury.com",             "Fintech & Digital Payments"),
    ("Klarna",              "klarna.com",              "Fintech & Digital Payments"),
    ("Navan",               "navan.com",               "Fintech & Digital Payments"),

    # ── Transportation & Frontier Tech ───────────────────────────────────────
    ("Tesla",               "tesla.com",               "Transportation & Frontier Tech"),
    ("Waymo",               "waymo.com",               "Transportation & Frontier Tech"),
    ("Aurora Innovation",   "aurora.tech",             "Transportation & Frontier Tech"),
    ("Zoox",                "zoox.com",                "Transportation & Frontier Tech"),
    ("Rivian",              "rivian.com",              "Transportation & Frontier Tech"),
    ("Applied Intuition",   "appliedintuition.com",    "Transportation & Frontier Tech"),
    ("Mobileye",            "mobileye.com",            "Transportation & Frontier Tech"),
    ("Joby Aviation",       "jobyaviation.com",        "Transportation & Frontier Tech"),
    ("SpaceX",              "spacex.com",              "Transportation & Frontier Tech"),
    ("Lucid Motors",        "lucidmotors.com",         "Transportation & Frontier Tech"),
]


def get_or_create_tab(sheet, title: str, index: int) -> gspread.Worksheet:
    try:
        return sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return sheet.add_worksheet(title=title, rows=1000, cols=20, index=index)


def setup(sheet_id: str):
    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)

    print("Setting up tabs...")

    # Tab 1 — Job Tracker
    ws1 = get_or_create_tab(sheet, TAB_JOB_TRACKER, 0)
    if not ws1.row_values(1):
        ws1.append_row(JOB_TRACKER_HEADERS)
    print(f"  ✓ {TAB_JOB_TRACKER}")

    # Tab 2 — Company List
    ws2 = get_or_create_tab(sheet, TAB_COMPANY_LIST, 1)
    ws2.clear()
    rows = [COMPANY_LIST_HEADERS]
    for name, domain, category in COMPANIES:
        rows.append([name, domain, category, "", "Yes", "", ""])
    ws2.update(rows, "A1")
    print(f"  ✓ {TAB_COMPANY_LIST} — {len(COMPANIES)} companies")

    # Tab 3 — Role Title Config
    ws3 = get_or_create_tab(sheet, TAB_TITLE_CONFIG, 2)
    ws3.clear()
    title_rows = [["Title"]] + [[t] for t in TARGET_TITLES]
    ws3.update(title_rows, "A1")
    print(f"  ✓ {TAB_TITLE_CONFIG} — {len(TARGET_TITLES)} titles")

    # Tab 4 — Run Log
    ws4 = get_or_create_tab(sheet, TAB_RUN_LOG, 3)
    if not ws4.row_values(1):
        ws4.append_row(RUN_LOG_HEADERS)
    print(f"  ✓ {TAB_RUN_LOG}")

    print(f"\nDone. Sheet ID: {sheet_id}")
    print("Next: fill in 'Careers Page URL' in Tab 2 for company-direct scraping.")


if __name__ == "__main__":
    missing = [v for v, k in [
        ("GOOGLE_SHEET_ID", GOOGLE_SHEET_ID),
        ("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID),
        ("GOOGLE_CLIENT_SECRET", GOOGLE_CLIENT_SECRET),
        ("GOOGLE_REFRESH_TOKEN", GOOGLE_REFRESH_TOKEN),
    ] if not k]
    if missing:
        print(f"Error: missing env vars: {', '.join(missing)}")
        sys.exit(1)
    setup(GOOGLE_SHEET_ID)
