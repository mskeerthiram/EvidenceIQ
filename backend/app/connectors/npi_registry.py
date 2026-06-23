"""
NPI Registry connector (npiregistry.cms.hhs.gov) — free, public, no API
key required. This is the project's "government licensing database"
source for the healthcare category, and the highest-trust source in
the reliability weight table.
"""
import httpx

from app.models import RawBusinessRecord

SOURCE_NAME = "npi_registry"
BASE_URL = "https://npiregistry.cms.hhs.gov/api/"


async def fetch_npi_registry(category: str, location: str, max_results: int = 30) -> list[RawBusinessRecord]:
    """
    `category` is matched loosely against NPI taxonomy descriptions
    (e.g. "cardiologist" will match "Cardiovascular Disease").
    `location` is split into city/state where possible — this source
    is naturally US-only, by design of the registry itself.
    """
    city, state = _split_location(location)
    params = {
        "version": "2.1",
        "city": city,
        "state": state,
        "limit": max_results,
        "taxonomy_description": category,
    }
    results: list[RawBusinessRecord] = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return results

    for entry in data.get("results", []):
        basic = entry.get("basic", {})
        addresses = entry.get("addresses", [])
        practice_addr = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None)

        name = basic.get("organization_name") or f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip()
        if not name:
            continue

        results.append(RawBusinessRecord(
            source=SOURCE_NAME,
            name=name,
            phone=practice_addr.get("telephone_number") if practice_addr else None,
            address=_flatten_address(practice_addr) if practice_addr else None,
            license_information=f"NPI #{entry.get('number')}",
            source_url=f"https://npiregistry.cms.hhs.gov/provider-view/{entry.get('number')}",
        ))

    return results


def _split_location(location: str) -> tuple[str, str]:
    parts = [p.strip() for p in location.split(",")]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return location, ""


def _flatten_address(addr: dict) -> str | None:
    parts = [addr.get("address_1"), addr.get("city"), addr.get("state"), addr.get("postal_code")]
    return ", ".join(p for p in parts if p) or None
