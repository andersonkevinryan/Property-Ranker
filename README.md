# InvestorSteroids (Listings Funnel + Criteria Engine)

A cloud‑friendly Streamlit app that **funnels, normalizes, filters, and scores property listings**
like a mini "Zillow for investors" with your **buy box** baked in.

## Key features
- **Ingest**: upload CSVs from Redfin, MLS, Realtor exports (bring your own data).
- **Normalize**: unify columns (price, rent, units, year built, sqft, address, city, state, zip).
- **Criteria Engine**: save reusable criteria like "4‑plex, 2000+ build, ≥ X sqft, ≤ $1,000,000, any market".
- **Scoring**: compute Price‑to‑Rent, cap rate (with your opex/tax/HOI hints), DSCR (with loan constant).
- **Search Links**: one‑click deep links to Zillow/Redfin/Realtor for fresh inventory (no scraping).
- **Database**: uses DuckDB in /tmp (ephemeral). Export/import DB snapshots as a CSV to persist.

## Run (all cloud work)
- Push this repo to GitHub, deploy on Streamlit Cloud or HuggingFace Spaces.
- No paid APIs required.

## Files
- `app.py` — Streamlit UI (criteria + listings + scoring + deep links)
- `ingest.py` — CSV normalizers for Redfin & generic MLS
- `kpis.py` — KPI math (P/R, cap, DSCR)
- `db.py` — small DuckDB helpers
- `schemas.py` — column maps for normalization
- `examples/` — sample CSVs and criteria YAMLs

## Disclaimer
Always verify taxes (assessor), insurance (bindable quotes), zoning, and legal compliance before offering.
No scraping is performed; this app builds links for you to run searches directly on public sites.
