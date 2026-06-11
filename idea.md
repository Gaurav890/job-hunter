Job Hunt Agent — System Brief

Agent Identity
This is a multi-agent using CrewAI runs autonomously on a scheduled basis to discover, score, filter, and surface relevant job opportunities for Gaurav Chaulagain — an AI Solutions / Forward Deployed PM candidate targeting US-based roles at $150K+ with visa sponsorship.

Schedule
Two runs per day:

Run 1: 6:00 AM PT — catches overnight and early morning postings
Run 2: 1:00 PM PT — catches same-day postings

Each run has a 2-hour execution window. Total daily runtime: 4 hours.

Target Role Titles
The agent searches for the following titles. This list is additive — new titles can be appended to a config sheet without changing agent logic:

AI Product Manager
Technical Product Manager
Forward Deployed Engineer
Forward Deployed Product Manager
AI Solutions Engineer
AI Solutions Architect
Agent Strategist
Enterprise AI Strategist
AI Implementation Manager
Solutions Engineer (AI)
Customer Success Engineer (AI)
AI Deployment Strategist


Geography Filter
United States only. Remote, hybrid, and on-site all acceptable. Exclude roles explicitly listed as outside the US.

Salary Filter
Minimum $150,000 base. Apply this filter where salary is disclosed. Do not reject roles where salary is not disclosed — flag them as "Salary Unknown" in the tracker.

Visa Sponsorship Logic
This is a two-tier check, executed in order:
Tier 1 — Job Posting Text (Fast Check)
Scan the job description for explicit sponsorship language:

Include if post says: "will sponsor", "visa sponsorship available", "sponsorship provided", "H1B sponsor", "open to sponsoring"
Exclude if post explicitly says: "no sponsorship", "must be authorized to work", "we do not sponsor visas", "US citizen or permanent resident only"
If no sponsorship language found → proceed to Tier 2

Tier 2 — Historical H1B Check (Verification)
Query myvisajobs.com and h1bdata.info for the company name. If the company has filed H1B petitions in the last 3 years → mark as "Likely Sponsors" and include. If no history found → mark as "Sponsorship Unknown" and still include, but flag clearly.
Do not run Tier 2 if Tier 1 already confirms sponsorship. Skip the lookup and mark as "Confirmed in Posting."

Job Sources
Search the following sources in priority order:
Primary (structured, most reliable):

LinkedIn Jobs
Greenhouse job boards (direct company career pages)
Lever job boards (direct company career pages)
Workday career portals (for enterprise companies on the target list)

Secondary (broader coverage):

Indeed
Glassdoor
Wellfound (for AI startups)
Builtin.com (SF, NY, remote filters)

Company-direct (highest priority):
For every company on the target company list, the agent visits the careers page directly each run and checks for new postings matching target titles. These bypass all aggregators.

Target Company List
The full list of 100+ companies provided by Gaurav across these categories: Enterprise Software & Cloud, Semiconductors & Hardware, Cybersecurity & Developer Tools, Internet & Social Media, Entertainment & Gaming, E-commerce & On-Demand, Fintech & Digital Payments, Transportation & Frontier Tech, AI & Tech Startups.
This list lives in a dedicated "Company List" tab in the Google Sheet. The agent reads from this tab every run. Gaurav adds companies to this tab and the agent picks them up automatically on the next run — no code changes required.

Scoring & Prioritization
Every job found gets a score from 0–100 before being written to the sheet. The agent ranks jobs by score descending.
SignalPointsCompany is on target list+30Title is an exact match to target titles+20Title is a close match (≥2 keywords overlap)+10Salary ≥ $150K confirmed+15Sponsorship confirmed in posting+15Sponsorship confirmed via H1B history+10Posted within last 24 hours+10Posted within last 72 hours+5Role is remote+5
Priority tiers based on score:

🔴 Priority 1 (score 70+): Apply same day
🟡 Priority 2 (score 50–69): Apply within 48 hours
🟢 Priority 3 (score 30–49): Review and decide
⚪ Hold (below 30): Archive, do not surface in main view


Google Sheet Structure
Tab 1: Job Tracker (Main View)
ColumnDescriptionDate FoundTimestamp of discoveryPriority🔴🟡🟢⚪Score0–100CompanyCompany nameRole TitleExact title from postingLocationCity / RemoteSalaryAs listed, or "Unknown"Sponsorship StatusConfirmed / Likely / Unknown / No SponsorPosted DateWhen the role was postedJob URLDirect link to postingSourceWhere it was foundStatusNew / Reviewing / Applied / Reached Out / Interview / Rejected / OfferApplication DateFilled in manually by GauravNotesFree textLinkedIn ContactsNames of relevant connections at that company (auto-populated)Outreach DraftAuto-generated message draft
Tab 2: Company List
ColumnDescriptionCompany NameDomainCategorye.g. AI Startup, Enterprise SaaSCareers Page URLDirect linkH1B HistoryYes / No / UnknownLast CheckedAuto-updated each runNotesManual field
Tab 3: Role Title Config
List of target job titles. Gaurav adds new titles here. Agent reads this on every run.
Tab 4: Run Log
ColumnDescriptionRun TimestampJobs FoundCountNew Jobs AddedCountCompanies CheckedCountErrorsAny failuresDurationMinutes taken

Deduplication Logic
Before writing any job to Tab 1, the agent checks:

Same company + same title + same location = duplicate → skip
Same job URL = duplicate → skip
If a role reappears but was previously marked "Rejected" or "Offer" → skip permanently


LinkedIn Integration
Read access used for two things:
1. Connection Mapping
For every job written to the tracker, the agent searches LinkedIn for people at that company who hold titles like:

Recruiter, Talent Acquisition, Engineering Manager, VP of Product, Head of AI, Director of Engineering

It cross-checks against Gaurav's connection list. Output written to the "LinkedIn Contacts" column:

If 1st connection found → flagged as "1st — reach out directly"
If 2nd connection found → flagged as "2nd — request intro or cold DM"
If no connection → flagged as "No connection — cold outreach"

2. Outreach Draft Generation
For each job row, the agent generates a short outreach message draft written to the "Outreach Draft" column. The draft follows this logic:

If 1st connection at company → warm message referencing the connection and the specific role
If recruiter/TA found → short recruiter-style DM referencing the role posting
If no connection → cold but specific DM referencing the role and one thing about the company

Draft tone: conversational, specific, not templated. Max 4 lines. Gaurav reviews and sends manually — the agent never sends autonomously.
Draft template structure:
Hey [Name], noticed [Company] is hiring for [Role Title]. 
[One specific sentence about why Gaurav is relevant — 
pulled from his background: Followloop, Cal Hacks win, 
FleetPanda deployment work]. Would love to learn more 
about the team. Open to a quick chat?

What the Agent Does NOT Do

Does not apply to jobs automatically
Does not send messages on LinkedIn
Does not store LinkedIn credentials — uses OAuth read access only
Does not surface roles with explicit "no sponsorship" language, ever
Does not re-score jobs Gaurav has already marked Applied, Interview, or Offer


Error Handling

If a careers page is down → log in Run Log, retry next run
If LinkedIn rate limit hit → pause LinkedIn lookup for that run, continue job scraping
If H1B lookup fails → mark sponsorship as "Unknown", do not block the job from appearing
If Google Sheet write fails → buffer results locally and retry at next run start


Tech Stack Recommendation
ComponentToolOrchestrationPython + APScheduler or PrefectWeb scrapingPlaywright (JS-heavy career pages) + BeautifulSoupLinkedIn accessLinkedIn API (read) or Playwright with session authH1B lookupmyvisajobs.com scraper + h1bdata.info scraperOutreach draft generationClaude API (Sonnet)Google Sheet read/writeGoogle Sheets API via gspreadStorageSupabase (dedup store + run logs)HostingRailway or Fly.io (always-on, runs on schedule)

Maintenance Interface
Gaurav controls the agent entirely through the Google Sheet:

Add a company → Tab 2
Add a role title → Tab 3
Change job status → Tab 1 Status column
Review run health → Tab 4 Run Log

No code changes needed for configuration updates.