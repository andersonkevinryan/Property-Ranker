import pandas as pd
from schemas import NORMALIZED_COLUMNS

def normalize_generic(df: pd.DataFrame) -> pd.DataFrame:
    # Attempt to coerce common columns; fall back to existing if already correct
    colmap = {}
    for c in df.columns:
        colmap[c.strip().lower()] = c

    def pick(*names):
        for n in names:
            if n in colmap: return df[colmap[n]]
        return None

    out = pd.DataFrame()
    out["source"] = pick("source") or "Upload"
    out["address"] = pick("address","street_address","property_address")
    out["city"] = pick("city","municipality")
    out["state"] = pick("state","region")
    out["zip"] = pick("zip","zipcode","postal_code")
    out["price"] = pd.to_numeric(pick("price","list_price","asking_price"), errors="coerce")
    out["monthly_rent"] = pd.to_numeric(pick("monthly_rent","rent","est_rent"), errors="coerce")
    out["units"] = pd.to_numeric(pick("units","unit_count"), errors="coerce")
    out["year_built"] = pd.to_numeric(pick("year_built","yr_built","built"), errors="coerce")
    out["sqft"] = pd.to_numeric(pick("sqft","square_feet","living_area"), errors="coerce")
    out["property_type"] = pick("property_type","type","prop_type")
    out["lat"] = pd.to_numeric(pick("lat","latitude"), errors="coerce")
    out["lon"] = pd.to_numeric(pick("lon","longitude","lng"), errors="coerce")
    out["notes"] = pick("notes","description","remarks")

    for c in NORMALIZED_COLUMNS:
        if c not in out.columns:
            out[c] = None

    return out[NORMALIZED_COLUMNS]
