"""
Core data model.

Every field of every business is represented as a Claim, not a raw
fact — it only carries weight once Evidence supports it. This object
is the foundation the whole "claims must earn trust" pitch is built on;
the live investigation feed in the frontend is literally this structure
rendered, not a separate presentation layer.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    VERIFIED = "Verified"
    CONTRADICTION_FOUND = "Contradiction Found"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"
    LIKELY = "Likely"


class EvidenceItem(BaseModel):
    source: str
    value: Optional[str] = None
    supports: bool = True
    reliability: float = 0.35
    freshness: float = 1.0
    url: Optional[str] = None


class Claim(BaseModel):
    field: str
    value: Optional[str] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)
    confidence: float = 0.0
    refute_score: float = 0.0
    verdict: Verdict = Verdict.INSUFFICIENT_EVIDENCE
    escalated: bool = False
    escalation_source_checked: Optional[str] = None


class RawBusinessRecord(BaseModel):
    """One record as returned by a single source connector, before
    it is converted into Claims and merged with other sources."""
    source: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None  # e.g. {"monday": "9:00 AM - 5:00 PM", ...}
    rating: Optional[float] = None
    review_count: Optional[int] = None
    services: List[str] = Field(default_factory=list)
    specialties: List[str] = Field(default_factory=list)
    license_information: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)
    social_profiles: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class Business(BaseModel):
    business_id: str
    business_name: str
    claims: List[Claim] = Field(default_factory=list)
    merged_from_sources: List[str] = Field(default_factory=list)


class SearchSummary(BaseModel):
    query: str
    businesses_found: int
    businesses_verified: int
    duplicate_records_removed: int
    sources_searched: int
    research_duration_seconds: float


class DataQualitySummary(BaseModel):
    pct_with_website: float
    pct_with_phone: float
    pct_with_hours: float
    pct_with_license: float


class SearchResult(BaseModel):
    summary: SearchSummary
    data_quality: DataQualitySummary
    businesses: List[Business]
    research_summary_text: Optional[str] = None
