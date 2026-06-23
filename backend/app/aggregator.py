"""
Claim Aggregator.
"""
from app.models import Claim, EvidenceItem, RawBusinessRecord

SOURCE_RELIABILITY = {
    "npi_registry": 0.95,
    "official_website": 0.85,
    "google_maps": 0.75,
    "google_business": 0.75,
    "linkedin": 0.65,
    "yelp": 0.60,
    "yellow_pages": 0.50,
    "duckduckgo": 0.40,
}
DEFAULT_RELIABILITY = 0.35


class BusinessCandidate:
    """A single raw record, claim-ified, before deduplication/merging."""

    def __init__(self, name: str, phone: str | None, address: str | None,
                 website: str | None, claims: list[Claim], source: str):
        self.name = name
        self.phone = phone
        self.address = address
        self.website = website
        self.claims = claims
        self.sources = [source]


def record_to_candidate(record: RawBusinessRecord, freshness: float = 1.0) -> BusinessCandidate:
    reliability = SOURCE_RELIABILITY.get(record.source, DEFAULT_RELIABILITY)
    claims: list[Claim] = []

    field_values = {
        "name": record.name,
        "phone": record.phone,
        "address": record.address,
        "email": record.email,
        "website": record.website,
        "rating": str(record.rating) if record.rating is not None else None,
        "license_information": record.license_information,
    }
    for field, value in field_values.items():
        if value:
            claims.append(_single_evidence_claim(field, value, record.source, reliability, freshness, record.source_url))

    if record.hours:
        for day, hours_value in record.hours.items():
            field = f"hours_{day.lower()}"
            claims.append(_single_evidence_claim(field, hours_value, record.source, reliability, freshness, record.source_url))

    return BusinessCandidate(
        name=record.name, phone=record.phone, address=record.address,
        website=record.website, claims=claims, source=record.source,
    )


def _single_evidence_claim(field: str, value: str, source: str, reliability: float,
                           freshness: float, url: str | None) -> Claim:
    return Claim(
        field=field,
        value=value,
        evidence=[EvidenceItem(source=source, value=value, supports=True,
                               reliability=reliability, freshness=freshness, url=url)],
    )