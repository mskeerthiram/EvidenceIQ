"""
Free search engine discovery connector (DuckDuckGo) — no API key needed.

Used for three things: general-purpose discovery of candidate
businesses, finding a business's official website, and a deliberately
narrow LinkedIn corroboration path.
"""
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from app.models import RawBusinessRecord

SOURCE_NAME = "duckduckgo"
SKIP_DOMAINS = ["yelp.com", "yellowpages.com", "facebook.com", "linkedin.com", "maps.google"]


def discover_official_site(business_name: str, location: str) -> str | None:
    query = f"{business_name} {location} official website"
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                url = r.get("href", "")
                if url and not any(skip in url for skip in SKIP_DOMAINS):
                    return url
    except Exception:
        pass
    return None


def discover_linkedin_snippet(business_name: str, location: str) -> str | None:
    query = f"{business_name} {location} site:linkedin.com/company"
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                if "linkedin.com" in r.get("href", ""):
                    return r.get("href")
    except Exception:
        pass
    return None


def discover_candidates(category: str, location: str, max_results: int = 30) -> list[RawBusinessRecord]:
    query = f"{category} in {location}"
    out: list[RawBusinessRecord] = []
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    name = r.get("title", "").split(" - ")[0].strip()
                    if name:
                        out.append(RawBusinessRecord(
                            source=SOURCE_NAME,
                            name=name,
                            website=r.get("href"),
                            source_url=r.get("href"),
                        ))
            break
        except Exception:
            pass
    return out


async def discover_official_site_direct(business_name: str, location: str) -> str | None:
    import httpx
    from urllib.parse import unquote
    query = f"{business_name} {location} official website"
    headers = {"User-Agent": "Mozilla/5.0 (EvidenceIQ research agent; hackathon project)"}
    try:
        async with httpx.AsyncClient(headers=headers, timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a.result__a"):
                href = a.get("href", "")
                if "uddg=" in href:
                    encoded = href.split("uddg=")[1].split("&")[0]
                    url = unquote(encoded)
                    if url and not any(skip in url for skip in SKIP_DOMAINS):
                        return url
    except Exception:
        pass
    return None
