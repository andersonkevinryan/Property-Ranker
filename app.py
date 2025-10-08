import streamlit as st
import pandas as pd
import numpy as np
import json
import yaml

from db import init_db, insert_listings, fetch_listings, fetch_listings_filtered, save_criteria, load_criteria
from ingest import normalize_generic
from kpis import price_to_rent, cap_rate, dscr

st.set_page_config(page_title="InvestorSteroids", layout="wide")
st.title("InvestorSteroids — Listings Funnel + Criteria Engine")

init_db()

with st.sidebar:
    st.header("Global KPI Inputs")
    loan_constant = st.number_input("Loan constant (annual debt / price)", value=0.081, help="~0.081 ≈ 30yr @ ~7.25%")
    opex_ratio_hint = st.number_input("Opex ratio hint", value=0.33)
    tax_annual_hint = st.number_input("Default annual taxes", value=4000)
    ins_annual_hint = st.number_input("Default annual insurance", value=1800)
    hoa_annual_hint = st.number_input("Default annual HOA", value=0)
    other_income_m_hint = st.number_input("Default other income (monthly)", value=50)

st.subheader("1) Ingest Listings (CSV)")
st.caption("Upload exports from Redfin / MLS / Realtor. We'll normalize them and store in a small DuckDB in /tmp.")
file = st.file_uploader("Upload CSV", type=["csv"])
if file:
    df = pd.read_csv(file)
    norm = normalize_generic(df)
    st.write("Preview normalized:")
    st.dataframe(norm.head(20), use_container_width=True)
    if st.button("Save to database"):
        insert_listings(norm.fillna(""))
        st.success(f"Inserted {len(norm)} listings.")

st.subheader("2) Define Criteria")
with st.expander("Build criteria"):
    cols = st.columns(3)
    with cols[0]:
        units_min = st.number_input("Units min", value=4)
        units_max = st.number_input("Units max", value=4)
        year_built_min = st.number_input("Year built min", value=2000)
    with cols[1]:
        sqft_min = st.number_input("Sqft min", value=0)
        price_min = st.number_input("Price min", value=0)
        price_max = st.number_input("Price max", value=1000000)
    with cols[2]:
        city = st.text_input("City filter (optional)")
        state = st.text_input("State filter (optional, 2-letter)")

    c_name = st.text_input("Save criteria as (name)", value="Fourplex_Newer_BuyBox")
    if st.button("Save criteria"):
        crit = {
            "units_min": units_min, "units_max": units_max,
            "year_built_min": year_built_min,
            "sqft_min": sqft_min,
            "price_min": price_min, "price_max": price_max,
            "city": city, "state": state,
            "loan_constant": loan_constant,
            "opex_ratio_hint": opex_ratio_hint,
            "tax_annual_hint": tax_annual_hint,
            "ins_annual_hint": ins_annual_hint,
            "hoa_annual_hint": hoa_annual_hint,
            "other_income_m_hint": other_income_m_hint,
        }
        save_criteria(c_name, json.dumps(crit))
        st.success("Saved.")

st.subheader("Saved Searches")
saved = load_criteria()
if not saved.empty:
    st.dataframe(saved[["id","name"]], use_container_width=True)
else:
    st.info("No saved searches yet.")

st.subheader("3) Run Search")
st.caption("We filter your DB, compute KPIs, and let you export.")

where = "1=1"
if st.checkbox("Use latest saved criteria", value=True) and not saved.empty:
    row = saved.iloc[0]  # latest
    crit = json.loads(row["criteria_json"])
    where += f" AND units >= {crit['units_min']} AND units <= {crit['units_max']}"
    where += f" AND year_built >= {crit['year_built_min']}"
    where += f" AND price >= {crit['price_min']} AND price <= {crit['price_max']}"
    if crit.get("sqft_min",0)>0:
        where += f" AND sqft >= {crit['sqft_min']}"
    if crit.get("city"):
        where += f" AND lower(city) = '{crit['city'].lower()}'"
    if crit.get("state"):
        where += f" AND upper(state) = '{crit['state'].upper()}'"
    # KPI hints
    loan_constant = crit.get("loan_constant", loan_constant)
    opex_ratio_hint = crit.get("opex_ratio_hint", opex_ratio_hint)
    tax_annual_hint = crit.get("tax_annual_hint", tax_annual_hint)
    ins_annual_hint = crit.get("ins_annual_hint", ins_annual_hint)
    hoa_annual_hint = crit.get("hoa_annual_hint", hoa_annual_hint)
    other_income_m_hint = crit.get("other_income_m_hint", other_income_m_hint)

df = fetch_listings_filtered(where) if 'where' in locals() else fetch_listings()

if df.empty:
    st.warning("No listings yet. Upload CSVs above.")
else:
    # KPIs
    df["price_to_rent"] = df.apply(lambda r: price_to_rent(r.get("price"), r.get("monthly_rent")), axis=1)
    df["cap_rate_est"] = df.apply(lambda r: cap_rate(r.get("price"), r.get("monthly_rent"),
                                                     other_income_m_hint, tax_annual_hint, ins_annual_hint,
                                                     hoa_annual_hint, opex_ratio_hint), axis=1)
    df["dscr_est"] = df.apply(lambda r: dscr(r.get("price"), r.get("monthly_rent"),
                                             other_income_m_hint, tax_annual_hint, ins_annual_hint,
                                             hoa_annual_hint, opex_ratio_hint, loan_constant), axis=1)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download filtered + KPIs (CSV)", df.to_csv(index=False).encode("utf-8"),
                       file_name="investor_filtered_listings.csv", mime="text/csv")

st.subheader("4) One‑click Search Links (fresh inventory)")
st.caption("We can't scrape, but we build deep‑links you can click into portals using your criteria.")
def zillow_link(city, state, price_max, year_min, units):
    # Zillow URL patterns change; keep it simple:
    # e.g., https://www.zillow.com/homes/for_sale/{city}-{state}/?searchQueryState=... (we'll approximate)
    base = f"https://www.zillow.com/homes/for_sale/{city}-{state}/"
    params = []
    if price_max: params.append(f"priceMax={int(price_max)}")
    if year_min: params.append(f"yearBuiltMin={int(year_min)}")
    # Zillow has limited multi-family filters via UI; user can refine after loading.
    return base + ("?" + "&".join(params) if params else "")

def redfin_link(city, state, price_max, year_min, units):
    base = f"https://www.redfin.com/city/"
    # Redfin city ID is not trivial; provide a generic search URL:
    q = f"{city}%2C%20{state}"
    return f"https://www.redfin.com/stingray/do/location-autocomplete?location={q}"

cols = st.columns(3)
with cols[0]:
    c_city = st.text_input("City (for link)", value="Indianapolis")
with cols[1]:
    c_state = st.text_input("State (2‑letter)", value="IN")
with cols[2]:
    c_price = st.number_input("Max price (for link)", value=1000000)
c_year = st.number_input("Min year built (for link)", value=2000)
c_units = st.number_input("Units (for link hint)", value=4)

st.write("Zillow:", zillow_link(c_city, c_state, c_price, c_year, c_units))
st.write("Redfin (start with autocomplete, refine in UI):", redfin_link(c_city, c_state, c_price, c_year, c_units))

st.info("Tip: After using these links, export matches from the portal as CSV and upload above to add them to your database for scoring.")
