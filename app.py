import streamlit as st
import pandas as pd
import yaml
from core.gates import hard_gate

st.set_page_config(page_title="InvestorEngine — Gate UI", layout="wide")
st.title("InvestorEngine — Institutional Hard Gates (Piece 1)")
st.caption("Every criterion is editable. Upload listings → see PASS/FAIL with explicit reasons.")

# --- Load default configs
def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

msa_options = {
    "Indianapolis (IN)": "config/msas/indianapolis.yaml",
    "Upstate SC (Greenville–Spartanburg)": "config/msas/upstate_sc.yaml",
}
msaname = st.selectbox("Choose MSA config", list(msa_options.keys()))
msa_cfg = load_yaml(msa_options[msaname])

buybox_cfg = load_yaml("config/buyboxes/fourplex_2000plus.yaml")

st.sidebar.header("MSA Gate Thresholds (editable)")
g = msa_cfg.get("gates", {})
col1, col2 = st.sidebar.columns(2)
with col1:
    rent_control = st.checkbox("Rent control present?", value=g.get("rent_control", False))
    eviction_weeks_max = st.number_input("Eviction weeks max", value=float(g.get("eviction_weeks_max", 9)), step=1.0)
    vacancy_max = st.number_input("Vacancy max", value=float(g.get("vacancy_max", 0.08)), step=0.005, format="%.3f")
    rent_to_income_max = st.number_input("Rent-to-income max", value=float(g.get("rent_to_income_max", 0.33)), step=0.01, format="%.2f")
with col2:
    hoi_pct_rc_max = st.number_input("HOI % of repl. cost (max)", value=float(g.get("hoi_pct_rc_max", 0.02)), step=0.005, format="%.3f")
    wind_hail_deductible_max = st.number_input("Wind/Hail deductible max", value=float(g.get("wind_hail_deductible_max", 0.02)), step=0.005, format="%.3f")
    dscr_min = st.number_input("DSCR min (stressed)", value=float(g.get("dscr_min", 1.30)), step=0.05, format="%.2f")
    pr_target_max = st.number_input("Price-to-Rent max", value=float(g.get("pr_target_max", 18.0)), step=0.5, format="%.1f")
cap_min = st.sidebar.number_input("Cap rate min", value=float(g.get("cap_min", 0.065)), step=0.005, format="%.3f")
rate_stress_bps = st.sidebar.number_input("Rate stress (+bps to loan constant)", value=50, step=25)

# Update the msa_cfg gates with UI values
msa_cfg["gates"].update({
    "rent_control": rent_control,
    "eviction_weeks_max": eviction_weeks_max,
    "vacancy_max": vacancy_max,
    "rent_to_income_max": rent_to_income_max,
    "hoi_pct_rc_max": hoi_pct_rc_max,
    "wind_hail_deductible_max": wind_hail_deductible_max,
    "dscr_min": dscr_min,
    "pr_target_max": pr_target_max,
    "cap_min": cap_min,
})

st.sidebar.header("Buy Box (editable)")
units_min = st.sidebar.number_input("Units min", value=int(buybox_cfg.get("units_min", 4)))
units_max = st.sidebar.number_input("Units max", value=int(buybox_cfg.get("units_max", 4)))
year_built_min = st.sidebar.number_input("Year built min", value=int(buybox_cfg.get("year_built_min", 2000)))
sqft_min = st.sidebar.number_input("Sqft min", value=int(buybox_cfg.get("sqft_min", 2800)))
price_max = st.sidebar.number_input("Price max", value=float(buybox_cfg.get("price_max", 1000000)), step=5000.0)
city = st.sidebar.text_input("City filter (optional)", value=str(buybox_cfg.get("city","")))
state = st.sidebar.text_input("State filter (2-letter, optional)", value=str(buybox_cfg.get("state","")))

st.sidebar.subheader("Financial Hints")
loan_constant = st.sidebar.number_input("Loan constant", value=float(buybox_cfg["financial"].get("loan_constant", 0.081)), step=0.001, format="%.3f")
opex_ratio_hint = st.sidebar.number_input("Opex ratio hint", value=float(buybox_cfg["financial"].get("opex_ratio_hint", 0.33)), step=0.01, format="%.2f")
tax_annual_hint = st.sidebar.number_input("Tax annual hint", value=float(buybox_cfg["financial"].get("tax_annual_hint", 4000)))
ins_annual_hint = st.sidebar.number_input("Insurance annual hint", value=float(buybox_cfg["financial"].get("ins_annual_hint", 1800)))
hoa_annual_hint = st.sidebar.number_input("HOA annual hint", value=float(buybox_cfg["financial"].get("hoa_annual_hint", 0)))
other_income_m_hint = st.sidebar.number_input("Other income monthly hint", value=float(buybox_cfg["financial"].get("other_income_m_hint", 50)))

# Write back to buybox
buybox_cfg.update({
    "units_min": units_min, "units_max": units_max,
    "year_built_min": year_built_min, "sqft_min": sqft_min,
    "price_max": price_max, "city": city, "state": state,
    "financial": {
        "loan_constant": loan_constant,
        "opex_ratio_hint": opex_ratio_hint,
        "tax_annual_hint": tax_annual_hint,
        "ins_annual_hint": ins_annual_hint,
        "hoa_annual_hint": hoa_annual_hint,
        "other_income_m_hint": other_income_m_hint,
    },
})

st.header("Upload Listings")
st.caption("CSV with columns like: address, city, state, zip, price, monthly_rent, units, year_built, sqft, [optional: vacancy_rate, hoi_pct_rc, wind_hail_deductible]")
uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    # Ensure expected cols exist
    for col in ["address","city","state","zip","price","monthly_rent","units","year_built","sqft"]:
        if col not in df.columns:
            df[col] = None

    st.write("Preview:", df.head(10))

    # Run gates
    results = []
    kpi_inputs = {"rate_stress_bps": rate_stress_bps}
    for _, row in df.iterrows():
        r = row.to_dict()
        gres = hard_gate(msa_cfg, buybox_cfg, r, kpi_inputs)
        results.append({
            "address": r.get("address"),
            "city": r.get("city"),
            "state": r.get("state"),
            "price": r.get("price"),
            "units": r.get("units"),
            "year_built": r.get("year_built"),
            "sqft": r.get("sqft"),
            "PASS": gres.passed,
            "reasons": "; ".join(gres.reasons) if gres.reasons else ""
        })
    out = pd.DataFrame(results)
    st.subheader("Gate Results")
    st.dataframe(out, use_container_width=True)
    st.download_button("Download PASS/FAIL (CSV)", out.to_csv(index=False).encode("utf-8"),
                       file_name="gate_results.csv", mime="text/csv")

st.divider()
st.markdown("**Next steps**: add Scoring for survivors, Evidence Pack, DSCR stress sliders, and saved searches.")

