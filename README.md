# EvidenceIQ

**Every fact must earn trust.**

An AI business research agent built for Chettinad CodeFest 2026 — Grand
Finale. Given a query like `"Cardiologists in Birmingham"`, it discovers
matching businesses across multiple free public sources, treats every
field as a *claim* that must be supported by evidence before it's
trusted, detects contradictions across sources, autonomously escalates
to one more source when evidence conflicts, and streams the whole
investigation live to the browser.

This repo is the implementation of the architecture described in
`EvidenceIQ_Complete_Build_Plan.pdf` — read that first if anything below
is unclear; it has the worked confidence-formula example, the full
source reliability table, and the day-by-day build plan this code follows.

## Quick start

```bash
cp .env.example .env        # optional: add ANTHROPIC_API_KEY for the LLM summary
docker compose up --build
```

- Backend: `http://localhost:8000` (try `http://localhost:8000/api/health`)
- Frontend: `http://localhost:5173`

No paid API keys are required to run this end-to-end. `ANTHROPIC_API_KEY`
is optional — without it, the Research Summary stage falls back to a
templated summary instead of an LLM-generated one.

## Running the backend without Docker

```bash
cd backend
pip install -r requirements.txt
playwright install chromium   # needed for the Google Maps connector
uvicorn app.main:app --reload
```

You'll need a local PostgreSQL instance and `DATABASE_URL` set accordingly
(see `.env.example`).

## Running the core logic tests

The dedup/confidence engine logic can be checked without any network
access or database:

```bash
cd backend
python3 test_core_logic.py
```

## Project structure

```
backend/
  app/
    models.py          # Claim / Evidence / Business data model
    query_parser.py     # "X in Y" -> (category, location)
    connectors/         # one module per source (Google Maps, official
                         # website, DuckDuckGo, Yellow Pages, NPI Registry)
    aggregator.py        # raw records -> single-evidence Claims
    dedup.py              # entity resolution / merging
    confidence.py          # the evidence-fusion formula + verdict thresholds
    summary.py              # LLM research-summary narrator (grounded, optional)
    db.py                    # PostgreSQL cache
    orchestrator.py           # ties every stage together, streams events
    main.py                    # FastAPI app, SSE endpoint
  test_core_logic.py            # offline sanity tests
frontend/
  src/
    App.jsx              # search state + SSE connection
    components/
      SearchScreen.jsx     # Screen 1
      ResultsScreen.jsx     # Screen 2 — live investigation feed
      BusinessCard.jsx       # per-business claim/evidence/verdict display
```

## Known limitations (be ready to mention these to judges)

- **Google Maps and Yellow Pages scraping selectors are fragile by
  nature.** Both sites change their DOM periodically. If a connector
  returns nothing, check the selectors in that file first — this is a
  known, explainable limitation of scraping (vs. a paid API), not a bug
  in the verification logic.
- **LinkedIn is only used as a public-search-snippet corroboration
  source.** The system never logs in or scrapes behind LinkedIn's
  authentication wall — see `connectors/search_engine.py`.
- **The LLM research summary is a narrator, not a researcher.** It is
  only allowed to describe data already present in the verified JSON —
  see `summary.py`. This keeps it compliant with the brief's "must not
  invent or estimate information" rule.
- **Escalation is capped at one additional source per claim**, to keep
  runtime and demo behavior predictable.
- **Deduplication is O(n²)** at hackathon-demo scale this is fine
  (hundreds of candidates); past a few thousand, add a blocking index
  before the pairwise comparison (noted in `dedup.py`).

## Pushing to your own GitHub repo

This was built in a sandboxed environment without GitHub write access,
so the last step is yours:

```bash
cd evidenceiq
git init
git add .
git commit -m "EvidenceIQ initial implementation"
git branch -M main
git remote add origin <your-empty-github-repo-url>
git push -u origin main
```
