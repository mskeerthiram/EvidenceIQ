"""
Verification & Confidence Engine.
"""
from app.models import Claim, EvidenceItem, Verdict

def _dedup_by_source(evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    seen = set()
    out = []
    for e in evidence:
        if e.source not in seen:
            seen.add(e.source)
            out.append(e)
    return out

def compute_claim_confidence(claim: Claim) -> Claim:
    # Fix Issue 3 & 4: Deduplicate the evidence list permanently for calculation AND UI display layers
    claim.evidence = _dedup_by_source(claim.evidence)

    if claim.value:
        agreeing = [e for e in claim.evidence if e.supports and e.value == claim.value]
        disagreeing = [e for e in claim.evidence if not e.supports or e.value != claim.value]
    else:
        agreeing, disagreeing = [], claim.evidence

    claim.confidence = _noisy_or(agreeing)
    claim.refute_score = _noisy_or(disagreeing)
    claim.verdict = _decide_verdict(claim.confidence, claim.refute_score, len(claim.evidence))
    return claim

def _noisy_or(evidence: list[EvidenceItem]) -> float:
    if not evidence:
        return 0.0
    product_term = 1.0
    for e in evidence:
        weight = max(0.0, min(1.0, e.reliability * e.freshness))
        product_term *= (1 - weight)
    return round(1 - product_term, 4)

def _decide_verdict(confidence: float, refute: float, evidence_count: int) -> Verdict:
    if confidence >= 0.90:
        return Verdict.VERIFIED
    if confidence >= 0.85 and refute <= 0.4 * confidence:
        return Verdict.VERIFIED
    if refute >= 0.6 * confidence and refute >= 0.5 and evidence_count >= 2:
        return Verdict.CONTRADICTION_FOUND
    if confidence < 0.5 and refute < 0.5 and evidence_count <= 1:
        return Verdict.INSUFFICIENT_EVIDENCE
    return Verdict.LIKELY

def needs_escalation(claim: Claim) -> bool:
    return claim.verdict == Verdict.CONTRADICTION_FOUND and not claim.escalated