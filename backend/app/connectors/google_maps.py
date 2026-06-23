"""
Google Maps connector.
"""
import re
from playwright.async_api import async_playwright
from app.models import RawBusinessRecord

SOURCE_NAME = "google_maps"


async def fetch_google_maps(category: str, location: str, max_results: int = 30) -> list[RawBusinessRecord]:
    query = f"{category} in {location}"
    results: list[RawBusinessRecord] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}", timeout=30000)
            await page.wait_for_selector('div[role="feed"]', timeout=15000)
        except Exception:
            await browser.close()
            return results

        feed = page.locator('div[role="feed"]')
        for _ in range(6):
            await feed.evaluate("el => el.scrollBy(0, 1200)")
            await page.wait_for_timeout(900)

        cards = await page.locator('div[role="feed"] > div > div[role="article"]').all()
        for card in cards[:max_results]:
            try:
                name = (await card.locator("div.fontHeadlineSmall").first.inner_text()).strip()
            except Exception:
                continue
            full_text = await card.inner_text()
            results.append(RawBusinessRecord(
                source=SOURCE_NAME,
                name=name,
                phone=_extract_phone(full_text),
                rating=_extract_rating(full_text)[0],
                review_count=_extract_rating(full_text)[1],
                source_url=page.url,
            ))
        await browser.close()
    return results


def _extract_phone(text: str) -> str | None:
    match = re.search(r"(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", text)
    return match.group(1) if match else None


def _extract_rating(text: str) -> tuple[float | None, int | None]:
    match = re.search(r"(\d\.\d)\s*\((\d+(?:,\d+)*)\)", text)
    if match:
        return float(match.group(1)), int(match.group(2).replace(",", ""))
    return None, None