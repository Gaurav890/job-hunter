import asyncio
import logging
import re

from playwright.async_api import async_playwright, Page

from models.job import Job
from tools.scrapers.base import title_match_score, is_us_location, make_absolute_url

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

_CAREERS_KEYWORDS = re.compile(
    r"\b(careers?|jobs?|join us|work with us|open roles?|opportunities|we.re hiring|positions?)\b",
    re.IGNORECASE,
)
_SEE_ALL_PATTERN = re.compile(
    r"\b(see all|view all|show all|load more|view more|show more|all (open )?roles?|all (open )?jobs?)\b",
    re.IGNORECASE,
)


async def _find_careers_link_on_page(page: Page, base_url: str) -> str | None:
    """Scan footer, nav, and header for any link that looks like a careers page."""
    candidates = []
    for selector in ("footer a", "nav a", "header a", "a[href*='career']", "a[href*='job']"):
        try:
            for link in await page.query_selector_all(selector):
                text = (await link.text_content() or "").strip()
                href = (await link.get_attribute("href")) or ""
                if _CAREERS_KEYWORDS.search(text) or _CAREERS_KEYWORDS.search(href):
                    abs_url = make_absolute_url(href, base_url)
                    if abs_url and abs_url not in candidates:
                        candidates.append(abs_url)
        except Exception:
            continue

    # Prefer links whose href explicitly contains /careers or /jobs
    for url in candidates:
        if re.search(r"/(careers|jobs)", url, re.IGNORECASE):
            return url
    return candidates[0] if candidates else None


async def _click_see_all_jobs(page: Page) -> None:
    """Click 'see all roles', 'load more', etc. buttons up to 3 times to expand listings."""
    for _ in range(3):
        clicked = False
        try:
            buttons = await page.query_selector_all("button, a[role='button'], a")
            for btn in buttons:
                text = (await btn.text_content() or "").strip()
                if _SEE_ALL_PATTERN.search(text):
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    clicked = True
                    break
        except Exception:
            pass
        if not clicked:
            break


async def _extract_jobs(page: Page, url: str, company_name: str, target_titles: list[str]) -> list[Job]:
    await page.goto(url, timeout=30000, wait_until="networkidle")
    await page.wait_for_timeout(2000)

    # Try to expand all visible job listings before scraping
    await _click_see_all_jobs(page)

    jobs = []
    seen_urls: set[str] = set()

    for link in await page.query_selector_all("a"):
        try:
            title = (await link.text_content() or "").strip()
            href = (await link.get_attribute("href")) or ""
        except Exception:
            continue

        title = " ".join(title.split())
        if not title or len(title) > 120 or len(title) < 5:
            continue

        exact, close = title_match_score(title, target_titles)
        if not exact and not close:
            continue

        abs_url = make_absolute_url(href, url)
        if not abs_url or abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)

        jobs.append(Job(
            company=company_name,
            title=title,
            location="Unknown",
            url=abs_url,
            source="Company Direct",
            is_on_target_list=True,
        ))

    return jobs


async def _scrape_async(
    company_name: str,
    careers_url: str,
    domain: str,
    target_titles: list[str],
) -> list[Job]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = await ctx.new_page()

        try:
            # If no careers URL was provided, crawl the homepage to find one
            if not careers_url and domain:
                homepage = f"https://{domain}"
                try:
                    await page.goto(homepage, timeout=20000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(1500)
                    found = await _find_careers_link_on_page(page, homepage)
                    if found:
                        logger.debug(f"Homepage crawl found careers link for {company_name}: {found}")
                        careers_url = found
                except Exception as e:
                    logger.debug(f"Homepage crawl failed [{company_name}]: {e}")

            if not careers_url:
                return []

            jobs = await _extract_jobs(page, careers_url, company_name, target_titles)
            return jobs
        except Exception as e:
            logger.warning(f"Company direct failed [{company_name}]: {e}")
            return []
        finally:
            await browser.close()


def scrape_company_direct(
    company_name: str,
    careers_url: str,
    target_titles: list[str],
    domain: str = "",
) -> list[Job]:
    try:
        return asyncio.run(_scrape_async(company_name, careers_url, domain, target_titles))
    except Exception as e:
        logger.warning(f"Company direct run error [{company_name}]: {e}")
        return []
