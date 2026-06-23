"""
Official website connector.

Strategy: try schema.org structured data first (clean, free, and the
highest-trust self-reported source — many business sites embed this
for SEO). Only fall back to plain-text heuristics when no structured
data is present.
"""
import json
import re

import httpx
from bs4 import BeautifulSoup

from app.models import RawBusinessRecord

SOURCE_NAME = "official_website"
HEADERS = {"User-Agent": "Mozilla/5.0 (EvidenceIQ research agent; hackathon project)"}

BUSINESS_TYPES = {
    "LocalBusiness", "MedicalBusiness", "Physician", "Attorney",
    "HomeAndConstructionBusiness", "Organization", "Dentist", "Store",
}


async def fetch_official_website(url: str) -> RawBusinessRecord | None:
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    structured = _parse_schema_org(soup)
    if structured:
        structured.source_url = url
        structured.website = structured.website or url
        return structured

    return _heuristic_extract(soup, url)


def _parse_schema_org(soup: BeautifulSoup) -> RawBusinessRecord | None:
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            types = item.get("@type", "")
            types = types if isinstance(types, list) else [types]
            if any(t in BUSINESS_TYPES for t in types):
                rating_block = item.get("aggregateRating") or {}
                return RawBusinessRecord(
                    source=SOURCE_NAME,
                    name=item.get("name", ""),
                    address=_flatten_address(item.get("address")),
                    phone=item.get("telephone"),
                    email=item.get("email"),
                    website=item.get("url"),
                    hours=_flatten_hours(item.get("openingHoursSpecification")),
                    rating=_safe_float(rating_block.get("ratingValue")),
                    review_count=_safe_int(rating_block.get("reviewCount")),
                )
    return None


def _heuristic_extract(soup: BeautifulSoup, url: str) -> RawBusinessRecord:
    text = soup.get_text(" ", strip=True)
    phone_match = re.search(r"(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", text)
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    return RawBusinessRecord(
        source=SOURCE_NAME,
        name=title,
        phone=phone_match.group(1) if phone_match else None,
        email=email_match.group(0) if email_match else None,
        website=url,
        source_url=url,
    )


def _flatten_address(addr) -> str | None:
    if not addr:
        return None
    if isinstance(addr, str):
        return addr
    parts = [addr.get("streetAddress"), addr.get("addressLocality"),
              addr.get("addressRegion"), addr.get("postalCode")]
    return ", ".join(p for p in parts if p) or None


def _flatten_hours(spec) -> dict | None:
    if not spec:
        return None
    spec = spec if isinstance(spec, list) else [spec]
    hours = {}
    for s in spec:
        if not isinstance(s, dict):
            continue
        days = s.get("dayOfWeek", [])
        days = days if isinstance(days, list) else [days]
        opens, closes = s.get("opens"), s.get("closes")
        for d in days:
            day_name = d.split("/")[-1] if isinstance(d, str) else str(d)
            hours[day_name] = f"{opens} - {closes}"
    return hours or None


def _safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
