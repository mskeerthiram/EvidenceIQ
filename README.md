# EvidenceIQ

EvidenceIQ is an evidence-based business research agent built for the Chettinad CodeFest 2026 Grand Finale.

Most business discovery tools collect information and present it as fact. EvidenceIQ takes a different approach: every piece of information is treated as a claim that must be supported by evidence before it is trusted.

Given a query such as **"Cardiologists in Birmingham"**, the system discovers relevant businesses from public sources, cross-checks information across independent providers, identifies contradictions, removes duplicate records, and produces a transparent research report with confidence scores backed by evidence.

---

## The Idea

Business information on the internet is often fragmented, inconsistent, and outdated. A phone number may differ across directories. Addresses may be incomplete. Multiple listings may represent the same business.

Rather than assuming any source is correct, EvidenceIQ asks a different question:

**How much evidence supports this claim?**

Every field—name, address, phone number, website, operating hours, credentials, and ratings—is evaluated independently. Confidence increases only when multiple reliable sources agree.

When sources conflict, the system performs one additional verification step and recalculates confidence using the new evidence.

The result is a system that explains not only *what it found*, but also *why it believes it is correct*.

---

## Key Features

### Multi-Source Discovery

EvidenceIQ gathers information from multiple public sources, including business directories, search engines, official websites, and public registries.

### Evidence-Based Verification

Each field is supported by explicit evidence. Users can inspect which sources contributed to a result and how confidence was calculated.

### Duplicate Resolution

Listings referring to the same business are merged automatically using entity-resolution techniques based on names, phone numbers, and location data.

### Contradiction Detection

Conflicting information is surfaced rather than hidden. The system identifies disagreements between sources and performs an additional verification step when necessary.

### Real-Time Investigation Feed

The verification process is streamed live to the frontend, allowing users to observe how evidence is collected, evaluated, and combined.

### Grounded Research Summaries

Research summaries are generated only from verified information already present in the evidence graph. The system does not invent facts or speculate beyond the available data.

---

## Confidence Model

EvidenceIQ uses an evidence-fusion model to combine support from multiple independent sources.

For a claim supported by multiple sources:

Confidence = 1 − ∏(1 − source_reliability)

Example:

* Google Maps: 0.75
* Official Website: 0.85

Confidence:

1 − (1 − 0.75)(1 − 0.85)

= 96.25%

This approach rewards corroboration while preventing any single source from dominating the final result.

---

## Technology Stack

### Backend

* FastAPI
* Python
* PostgreSQL
* Playwright
* BeautifulSoup
* HTTPX

### Frontend

* React
* Vite

### Infrastructure

* Docker
* Docker Compose

### Data Processing

* RapidFuzz
* phonenumbers

---

## Running the Project

### Using Docker

```bash
cp .env.example .env
docker compose up --build
```

Backend:
http://localhost:8000

Frontend:
http://localhost:5173

### Local Development

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

A PostgreSQL instance is required. Configure `DATABASE_URL` in `.env`.

---

## Project Structure

* `connectors/` — source-specific data collection modules
* `aggregator.py` — converts raw records into structured claims
* `dedup.py` — entity resolution and duplicate detection
* `confidence.py` — evidence fusion and confidence scoring
* `orchestrator.py` — workflow coordination and streaming
* `summary.py` — grounded research summary generation

---

## Current Limitations

* Public websites and directories change their structure over time, which can require periodic updates to scraping logic.
* Escalation is intentionally limited to one additional verification step to maintain predictable runtime during demonstrations.
* The current deduplication strategy is designed for hundreds of businesses and would require indexing strategies for significantly larger datasets.

---

## Why EvidenceIQ?

Most research tools answer a question.

EvidenceIQ shows the evidence behind the answer.

The goal is not simply to collect information, but to establish trust in the information that is collected.
