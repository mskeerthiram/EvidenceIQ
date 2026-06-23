"""
Pipeline orchestrator.
"""
import asyncio
import time

from app.aggregator import record_to_candidate
from app.confidence import compute_claim_confidence, needs_escalation
from app.connectors.directories import fetch_yellow_pages
from app.connectors.google_maps import fetch_google_maps
from app.connectors.npi_registry import fetch_npi_registry
from app.connectors.official_website import fetch_official_website
from app.connectors.search_engine import discover_candidates, discover_linkedin_snippet, discover_official_site_direct as discover_official_site
from app.dedup import deduplicate
from app.db import get_cached_result, save_cached_result
from app.models import Business, DataQualitySummary, EvidenceItem, RawBusinessRecord, SearchResult, SearchSummary
from app.query_parser import parse_query
from app.summary import generate_research_summary

LINKEDIN_RELIABILITY = 0.65
MAX_ENRICHMENT_CANDIDATES = 5


async def run_search(query: str, force_refresh: bool = False):
    start = time.time()

    if not force_refresh:
        cached, age_days = get_cached_result(query)
        if cached:
            yield {"type": "cache_hit", "age_days": age_days}
            yield {"type": "done", "result": cached}
            return

    category, location = parse_query(query)
    yield {"type": "parsed", "category": category, "location": location}

    sources_used: list[str] = []
    raw_records: list[RawBusinessRecord] = []

    fetch_tasks = {
        "google_maps": fetch_google_maps(category, location),
        "yellow_pages": fetch_yellow_pages(category, location),
        "npi_registry": fetch_npi_registry(category, location),
        "duckduckgo": asyncio.to_thread(discover_candidates, category, location),
    }

    for name, task in fetch_tasks.items():
        try:
            records = await task
            raw_records.extend(records)
            sources_used.append(name)
            yield {"type": "source_complete", "source": name, "count": len(records)}
        except Exception as e:
            yield {"type": "source_failed", "source": name, "error": str(e)}

    # Enrich top candidates with their official website (schema.org data).
    enriched: list[RawBusinessRecord] = list(raw_records)
    enrich_count = 0
    for record in raw_records[:MAX_ENRICHMENT_CANDIDATES]:
        try:
            site_url = record.website or await discover_official_site(record.name, location)
            if site_url:
                site_record = await fetch_official_website(site_url)
                if site_record:
                    site_record.name = record.name
                    enriched.append(site_record)
                    enrich_count += 1
            # Fix Issue 3: Increased delay to 2.5s to explicitly protect the pipeline from DDG rate-limiting
            await asyncio.sleep(2.5)
        except Exception:
            continue
    if enrich_count and "official_website" not in sources_used:
        sources_used.append("official_website")
    yield {"type": "source_complete", "source": "official_website", "count": enrich_count}

    candidates = [record_to_candidate(r) for r in enriched]
    businesses = deduplicate(candidates)
    duplicates_removed = max(0, len(candidates) - len(businesses))

    verified_count = 0
    for business in businesses:
        for i, claim in enumerate(business.claims):
            business.claims[i] = compute_claim_confidence(claim)

        for i, claim in enumerate(business.claims):
            if needs_escalation(claim):
                linkedin_url = discover_linkedin_snippet(business.business_name, location)
                if linkedin_url:
                    claim.evidence.append(EvidenceItem(
                        source="linkedin", value=claim.value, supports=True,
                        reliability=LINKEDIN_RELIABILITY, freshness=1.0, url=linkedin_url,
                    ))
                    claim.escalated = True
                    claim.escalation_source_checked = "linkedin"
                    business.claims[i] = compute_claim_confidence(claim)
                    yield {"type": "escalation", "business": business.business_name, "field": claim.field}

        if any(c.verdict == "Verified" for c in business.claims):
            verified_count += 1

        yield {"type": "business_resolved", "business": business.model_dump()}

    summary = SearchSummary(
        query=query,
        businesses_found=len(businesses),
        businesses_verified=verified_count,
        duplicate_records_removed=duplicates_removed,
        sources_searched=len(sources_used),
        research_duration_seconds=round(time.time() - start, 2),
    )
    data_quality = _compute_data_quality(businesses)

    result = SearchResult(summary=summary, data_quality=data_quality, businesses=businesses)
    result.research_summary_text = generate_research_summary(result)

    result_dict = result.model_dump()
    save_cached_result(query, result_dict)

    yield {"type": "done", "result": result_dict}


def _compute_data_quality(businesses: list[Business]) -> DataQualitySummary:
    total = len(businesses) or 1

    def pct(field_name: str) -> float:
        count = sum(1 for b in businesses if any(c.field == field_name and c.value for c in b.claims))
        return round(100 * count / total, 1)

    return DataQualitySummary(
        pct_with_website=pct("website"),
        pct_with_phone=pct("phone"),
        pct_with_hours=pct("hours_monday"),
        pct_with_license=pct("license_information"),
    )