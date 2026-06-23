"""
Yellow Pages directory connector.

Lower trust source on purpose (see the reliability weight table in the
build plan) — used as one more corroborating, or contradicting, signal
for the confidence formula rather than a primary source.
"""
import httpx
from bs4 import BeautifulSoup

from app.models import RawBusinessRecord

SOURCE_NAME = "yellow_pages"
HEADERS = {"User-Agent": "Mozilla/5.0 (EvidenceIQ research agent; hackathon project)"}


async def fetch_yellow_pages(category: str, location: str, max_results: int = 20) -> list[RawBusinessRecord]:
    url = "https://www.yell.com/ucs/UcsSearchAction.do"
    params = {"keywords": category, "location": location}
    results: list[RawBusinessRecord] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        listings = soup.select("article.businessCapsule")[:max_results]
        for listing in listings:
            name_el = listing.select_one("h2.businessCapsule--name")
            if not name_el:
                continue
            phone_el = listing.select_one("span.businessCapsule--phone")
            address_el = listing.select_one("span.businessCapsule--address")
            results.append(RawBusinessRecord(
                source=SOURCE_NAME,
                name=name_el.get_text(strip=True),
                phone=phone_el.get_text(strip=True) if phone_el else None,
                address=address_el.get_text(strip=True) if address_el else None,
                source_url=resp.url,
            ))
    except Exception:
        pass
    return results