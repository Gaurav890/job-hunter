import asyncio
import logging

from playwright.async_api import async_playwright, Page

from models.job import Job
from tools.scrapers.base import title_match_score, is_us_location, make_absolute_url

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


async def _extract_jobs(page: Page, url: str, company_name: str, target_titles: list[str]) -> list[Job]:
    await page.goto(url, timeout=30000, wait_until="networkidle")
    await page.wait_for_timeout(2000)

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


def scrape_company_direct(company_name: str, careers_url: str, target_titles: list[str]) -> list[Job]:
    async def run() -> list[Job]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=UA)
            page = await ctx.new_page()
            try:
                jobs = await _extract_jobs(page, careers_url, company_name, target_titles)
            except Exception as e:
                logger.warning(f"Company direct failed [{company_name}]: {e}")
                jobs = []
            finally:
                await browser.close()
            return jobs

    try:
        return asyncio.run(run())
    except Exception as e:
        logger.warning(f"Company direct run error [{company_name}]: {e}")
        return []
