"""
Quick sanity test for the core logic (no network required):
query parsing, the confidence formula, and deduplication/merging.
Run with: python3 test_core_logic.py
"""
import sys
sys.path.insert(0, ".")

from app.query_parser import parse_query
from app.models import RawBusinessRecord
from app.aggregator import record_to_candidate
from app.dedup import deduplicate, normalize_phone, normalize_address
from app.confidence import compute_claim_confidence


def test_query_parser():
    assert parse_query("Cardiologists in Birmingham") == ("Cardiologists", "Birmingham")
    assert parse_query("Family Lawyers in Chicago") == ("Family Lawyers", "Chicago")
    print("[OK] query_parser")


def test_confidence_formula():
    # Worked example from the build plan: Yellow Pages (0.50) -> Google (0.75) -> Website (0.85)
    from app.models import Claim, EvidenceItem

    claim = Claim(field="phone", value="205-111-1111", evidence=[
        EvidenceItem(source="yellow_pages", value="205-111-1111", supports=True, reliability=0.50, freshness=1.0),
    ])
    claim = compute_claim_confidence(claim)
    assert abs(claim.confidence - 0.50) < 0.001, f"expected ~0.50, got {claim.confidence}"

    claim.evidence.append(EvidenceItem(source="google_business", value="205-111-1111", supports=True, reliability=0.75, freshness=1.0))
    claim = compute_claim_confidence(claim)
    assert abs(claim.confidence - 0.875) < 0.001, f"expected ~0.875, got {claim.confidence}"

    claim.evidence.append(EvidenceItem(source="official_website", value="205-111-1111", supports=True, reliability=0.85, freshness=1.0))
    claim = compute_claim_confidence(claim)
    assert abs(claim.confidence - 0.98125) < 0.001, f"expected ~0.98125, got {claim.confidence}"
    assert claim.verdict == "Verified", f"expected Verified, got {claim.verdict}"
    print(f"[OK] confidence formula climbs 0.50 -> 0.875 -> {claim.confidence} (Verified)")

    # Contradiction case
    contra = Claim(field="phone", value="205-222-2222", evidence=[
        EvidenceItem(source="yellow_pages", value="205-222-2222", supports=True, reliability=0.50, freshness=1.0),
        EvidenceItem(source="official_website", value="205-333-4444", supports=False, reliability=0.85, freshness=1.0),
    ])
    contra = compute_claim_confidence(contra)
    assert contra.verdict == "Contradiction Found", f"expected Contradiction Found, got {contra.verdict}"
    print(f"[OK] contradiction detected (confidence={contra.confidence}, refute={contra.refute_score})")


def test_dedup():
    assert normalize_phone("(205) 111-1111") == normalize_phone("205-111-1111")
    assert normalize_address("123 Elm Street") == normalize_address("123 elm st")

    records = [
        RawBusinessRecord(source="google_maps", name="ABC Heart Clinic", phone="(205) 111-1111", address="123 Elm Street, Birmingham"),
        RawBusinessRecord(source="official_website", name="ABC Cardiology Center", phone="205-111-1111", address="123 Elm St, Birmingham"),
        RawBusinessRecord(source="npi_registry", name="XYZ Dental", phone="(205) 999-0000", address="55 Oak Ave, Birmingham"),
    ]
    candidates = [record_to_candidate(r) for r in records]
    businesses = deduplicate(candidates)

    assert len(businesses) == 2, f"expected 2 distinct businesses after merge, got {len(businesses)}"
    merged = next(b for b in businesses if "ABC" in b.business_name)
    phone_claim = next(c for c in merged.claims if c.field == "phone")
    assert len(phone_claim.evidence) == 2, f"expected 2 merged evidence items, got {len(phone_claim.evidence)}"
    print(f"[OK] dedup merged 2 ABC records into 1 business with {len(phone_claim.evidence)} evidence items on phone")
    print(f"[OK] dedup correctly kept XYZ Dental separate ({len(businesses)} total businesses)")


if __name__ == "__main__":
    test_query_parser()
    test_confidence_formula()
    test_dedup()
    print("\nALL CORE LOGIC TESTS PASSED")
