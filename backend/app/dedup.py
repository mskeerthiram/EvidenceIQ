"""
Deduplication / entity resolution.
"""
import re
import phonenumbers
from rapidfuzz import fuzz

from app.aggregator import BusinessCandidate
from app.models import Business, Claim

NAME_SIMILARITY_THRESHOLD = 85

def normalize_phone(phone: str | None, region: str = "US") -> str | None:
    if not phone:
        return None
    try:
        parsed = phonenumbers.parse(phone, region)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        digits = re.sub(r"\D", "", phone)
        return digits or None

def normalize_address(address: str | None) -> str | None:
    if not address:
        return None
    addr = address.lower()
    addr = re.sub(r"[^\w\s]", "", addr)
    replacements = {
        "street": "st", "avenue": "ave", "boulevard": "blvd",
        "drive": "dr", "road": "rd", "suite": "ste",
    }
    for full, abbr in replacements.items():
        addr = addr.replace(full, abbr)
    return " ".join(addr.split()) or None

def _clean_name_for_matching(name: str) -> str:
    """
    Strips web title artifacts ('Home -', 'Welcome to', SEO titles)
    so name similarity matches clean directory records without lowering the
    strict threshold required to separate co-located practitioners.
    """
    if not name:
        return ""
    n = name.lower().strip()
    # Strip common title junk prefixes
    n = re.sub(r"^(home|welcome|index)\s*[-\s:]+\s*", "", n)
    n = re.sub(r"^(home|welcome|index)\s+to\s+", "", n)
    # Strip trailing marketing descriptions following pipes or distinct dash marks
    if " | " in n:
        n = n.split(" | ")[0]
    if " - " in n:
        n = n.split(" - ")[0]
    return n.strip()

def deduplicate(candidates: list[BusinessCandidate]) -> list[Business]:
    n = len(candidates)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    norm_phones = [normalize_phone(c.phone) for c in candidates]
    norm_addrs = [normalize_address(c.address) for c in candidates]

    for i in range(n):
        for j in range(i + 1, n):
            same_phone = norm_phones[i] and norm_phones[i] == norm_phones[j]
            same_addr = norm_addrs[i] and norm_addrs[i] == norm_addrs[j]

        if same_phone:
                name_similarity = fuzz.token_sort_ratio(
                    _clean_name_for_matching(candidates[i].name),
                    _clean_name_for_matching(candidates[j].name)
                )
                if name_similarity >= NAME_SIMILARITY_THRESHOLD:
                    union(i, j)
        elif same_addr:
                name_similarity = fuzz.token_sort_ratio(
                    _clean_name_for_matching(candidates[i].name),
                    _clean_name_for_matching(candidates[j].name)
                )
                if name_similarity >= NAME_SIMILARITY_THRESHOLD:
                    union(i, j)
        else:
                

                name_similarity = fuzz.token_sort_ratio(
                    _clean_name_for_matching(candidates[i].name),
                    _clean_name_for_matching(candidates[j].name)
                )
                if name_similarity >= 95:
                    union(i, j)
    groups: dict[int, list[BusinessCandidate]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(candidates[i])

    return [_merge_group(group, business_id=f"biz_{idx:04d}") for idx, group in enumerate(groups.values())]

def _merge_group(group: list[BusinessCandidate], business_id: str) -> Business:
    # Fix Issue 4: Prioritize clean names from structured directories over raw website markup
    structured_candidates = [
        c for c in group 
        if not any(s in ["official_website", "duckduckgo"] for s in c.sources)
    ]
    
    if structured_candidates:
        best_candidate = max(structured_candidates, key=lambda c: len(c.name or ""))
    else:
        best_candidate = max(group, key=lambda c: len(c.name or ""))
        
    best_name = best_candidate.name
    # Fallback defensive scrub to ensure presentation is polished for UI
    best_name = re.sub(r"^(Home|Welcome|Index)\s*[-\s:]+\s*", "", best_name, flags=re.IGNORECASE)
    if " | " in best_name:
        best_name = best_name.split(" | ")[0].strip()
        
    claims_by_field: dict[str, Claim] = {}

    for candidate in group:
        for claim in candidate.claims:
            if claim.field not in claims_by_field:
                claims_by_field[claim.field] = Claim(
                    field=claim.field, value=claim.value, evidence=list(claim.evidence)
                )
            else:
                existing = claims_by_field[claim.field]
                existing.evidence.extend(claim.evidence)
                if not existing.value:
                    existing.value = claim.value

    return Business(
        business_id=business_id,
        business_name=best_name,
        claims=list(claims_by_field.values()),
        merged_from_sources=list({s for c in group for s in c.sources}),
    )