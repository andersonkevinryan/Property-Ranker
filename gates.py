from dataclasses import dataclass
from typing import Dict, Any, List
import math

@dataclass
class GateResult:
    passed: bool
    reasons: List[str]

def _add_reason(reasons, cond, message):
    if not cond:
        reasons.append(message)

def hard_gate(msa_cfg: Dict[str,Any], buybox: Dict[str,Any], row: Dict[str,Any], kpi_inputs: Dict[str,Any]) -> GateResult:
    reasons = []
    g = msa_cfg.get("gates", {})
    fin = buybox.get("financial", {})

    # Normalize inputs (row fields may be NaN/None)
    def val(name, default=None):
        v = row.get(name, default)
        try:
            if v is None: return default
            return float(v)
        except Exception:
            return default

    # A) MSA-level gates (policy/market proxies) - use UI values passed in kpi_inputs to approximate
    _add_reason(reasons, not g.get("rent_control", False), "Rent control present")
    # Vacancy proxy (from upload or external enrichment; here we accept 'vacancy_rate' column if provided)
    vac = val("vacancy_rate", 0.06)
    _add_reason(reasons, vac <= g.get("vacancy_max", 0.08), f"Vacancy too high: {vac:.2%}")

    # B) Buy-box gates (asset)
    units = val("units", 0)
    year_built = val("year_built", 0)
    sqft = val("sqft", 0)
    price = val("price", math.inf)

    _add_reason(reasons, units >= buybox.get("units_min", 0), f"Units < min ({units} < {buybox.get('units_min')})")
    _add_reason(reasons, units <= buybox.get("units_max", 9999), f"Units > max ({units} > {buybox.get('units_max')})")
    _add_reason(reasons, year_built >= buybox.get("year_built_min", 0), f"Year built < min ({year_built} < {buybox.get('year_built_min')})")
    _add_reason(reasons, sqft >= buybox.get("sqft_min", 0), f"Sqft < min ({sqft} < {buybox.get('sqft_min')})")
    _add_reason(reasons, price <= buybox.get("price_max", math.inf), f"Price > max ({price} > {buybox.get('price_max')})")

    # City/State optional filters
    city = (buybox.get("city") or "").strip().lower()
    state = (buybox.get("state") or "").strip().upper()
    rcity = (str(row.get("city") or "")).strip().lower()
    rstate = (str(row.get("state") or "")).strip().upper()
    if city:
        _add_reason(reasons, rcity == city, f"City mismatch ({rcity} != {city})")
    if state:
        _add_reason(reasons, rstate == state, f"State mismatch ({rstate} != {state})")

    # C) Financial gates (P/R, Cap, DSCR) using quick hints
    monthly_rent = val("monthly_rent", 0)
    other_inc_m = fin.get("other_income_m_hint", 0)
    opex_ratio = fin.get("opex_ratio_hint", 0.33)
    taxes_y = fin.get("tax_annual_hint", 4000)
    ins_y = fin.get("ins_annual_hint", 1800)
    hoa_y = fin.get("hoa_annual_hint", 0)
    loan_constant = fin.get("loan_constant", 0.081)

    # Price-to-Rent
    pr = price/((monthly_rent or 0)*12.0) if monthly_rent else float('inf')
    _add_reason(reasons, pr <= g.get("pr_target_max", 18.0), f"Price-to-Rent too high ({pr:.1f} > {g.get('pr_target_max')})")

    # Cap
    annual_rent = (monthly_rent or 0)*12.0
    other_inc_y = (other_inc_m or 0)*12.0
    opex = (annual_rent + other_inc_y) * (opex_ratio or 0.33)
    noi = (annual_rent + other_inc_y) - (opex + taxes_y + ins_y + hoa_y)
    cap = (noi/price) if price and price>0 else 0
    _add_reason(reasons, cap >= g.get("cap_min", 0.065), f"Cap too low ({cap:.3f} < {g.get('cap_min')})")

    # DSCR (stressed: add +50 bps to loan constant if checkbox in UI)
    stressed_const = loan_constant * (1.0 + (kpi_inputs.get("rate_stress_bps", 50)/10000.0))
    ads = price * stressed_const
    dscr = (noi/ads) if ads>0 else 0
    _add_reason(reasons, dscr >= g.get("dscr_min", 1.30), f"DSCR too low ({dscr:.2f} < {g.get('dscr_min')})")

    # Insurance guardrails (if listing has columns like hoi_pct_rc or ded_wind_hail)
    hoi_pct_rc = val("hoi_pct_rc", 0.015)   # % of replacement cost proxy
    _add_reason(reasons, hoi_pct_rc <= g.get("hoi_pct_rc_max", 0.02), f"HOI > {g.get('hoi_pct_rc_max')*100:.0f}% RC ({hoi_pct_rc*100:.1f}%)")
    ded = val("wind_hail_deductible", 0.02)
    _add_reason(reasons, ded <= g.get("wind_hail_deductible_max", 0.02), f"Wind/Hail deductible > {g.get('wind_hail_deductible_max')*100:.0f}% ({ded*100:.1f}%)")

    passed = len([r for r in reasons if r.startswith("FAIL")]) == 0 and all([not msg for msg in []])
    # we treated reasons as plain messages; passed means none of the add_reason checks failed
    # Determine pass by whether any messages exist (messages indicate a failure)
    passed = (len(reasons) == 0)
    return GateResult(passed=passed, reasons=reasons)
