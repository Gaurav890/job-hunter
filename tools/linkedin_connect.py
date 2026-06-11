"""
LinkedIn connection mapper.

Uses a stored li_at session cookie with Playwright to find 1st/2nd degree
connections at a company who hold recruiter or hiring-manager titles.
Gracefully degrades to "No connection" on any failure or missing cookie.
"""

import asyncio
import logging

from playwright.async_api import async_playwright, BrowserContext, Page

from config.settings import LINKEDIN_COOKIE_LI_AT

logger = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

RECRUITER_KEYWORDS = [
    "recruiter", "talent acquisition", "technical recruiter",
    "engineering manager", "vp of product", "head of ai",
    "director of engineering", "engineering recruiter",
]


async def _inject_cookie(context: BrowserContext) -> None:
    await context.add_cookies([{
        "name": "li_at",
        "value": LINKEDIN_COOKIE_LI_AT,
        "domain": ".linkedin.com",
        "path": "/",
        "httpOnly": True,
        "secure": True,
    }])


async def _extract_contacts(page: Page) -> list[tuple[str, str]]:
    """Returns list of (name, degree) tuples from people search results."""
    contacts: list[tuple[str, str]] = []
    try:
        # Wait for result cards
        await page.wait_for_selector("li.reusable-search__result-container", timeout=8000)
        cards = await page.query_selector_all("li.reusable-search__result-container")

        for card in cards[:15]:
            text = (await card.text_content() or "").strip()
            text_lower = text.lower()

            # Only surface recruiter / hiring manager titles
            if not any(kw in text_lower for kw in RECRUITER_KEYWORDS):
                continue

            degree = ""
            if "1st" in text:
                degree = "1st"
            elif "2nd" in text:
                degree = "2nd"
            else:
                continue  # skip 3rd+ connections

            # Extract name (first aria-hidden span tends to be the name)
            name_el = await card.query_selector("span[aria-hidden='true']")
            name = (await name_el.text_content() or "").strip() if name_el else ""
            if name and len(name) > 2:
                contacts.append((name, degree))

    except Exception as e:
        logger.debug(f"Contact extraction error: {e}")

    return contacts


async def _search_company(company_name: str, slug: str) -> str:
    """Navigates LinkedIn people search and returns a contact info string."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UA)
        await _inject_cookie(context)
        page = await context.new_page()

        try:
            # Try company /people/ page first
            url = f"https://www.linkedin.com/company/{slug}/people/"
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)

            if "authwall" in page.url or "login" in page.url:
                logger.warning("LinkedIn li_at cookie expired — needs refresh")
                return "Session expired — refresh LINKEDIN_COOKIE_LI_AT"

            contacts = await _extract_contacts(page)

            # If company page had no results, try people search
            if not contacts:
                search_url = (
                    f"https://www.linkedin.com/search/results/people/"
                    f"?keywords={slug}+recruiter&network=%5B%22F%22%2C%22S%22%5D"
                )
                await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)
                contacts = await _extract_contacts(page)

            if not contacts:
                return "No connection — cold outreach"

            # Prefer 1st degree; otherwise take first 2nd
            first_deg = [(n, d) for n, d in contacts if d == "1st"]
            second_deg = [(n, d) for n, d in contacts if d == "2nd"]

            if first_deg:
                names = ", ".join(n for n, _ in first_deg[:2])
                return f"1st — {names} — reach out directly"
            elif second_deg:
                names = ", ".join(n for n, _ in second_deg[:2])
                return f"2nd — {names} — request intro or cold DM"

            return "No connection — cold outreach"

        except Exception as e:
            logger.warning(f"LinkedIn search failed [{company_name}]: {e}")
            return "No connection — cold outreach"
        finally:
            await browser.close()


def find_linkedin_connections(company_name: str, domain: str) -> str:
    """Synchronous entry point. Returns connection info string."""
    if not LINKEDIN_COOKIE_LI_AT:
        return "No connection — cold outreach"

    slug = domain.split(".")[0].lower() if domain else company_name.lower().replace(" ", "-")

    try:
        return asyncio.run(_search_company(company_name, slug))
    except Exception as e:
        logger.warning(f"LinkedIn run error [{company_name}]: {e}")
        return "No connection — cold outreach"
