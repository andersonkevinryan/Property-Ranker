# Simple source column maps — extend these as you encounter new exports.

RED_FIN_MAP = {
    # Example: Redfin often uses 'PRICE', 'BEDS', 'BATHS', 'ADDRESS' etc.
    # For our sample we assume CSV already normalized; this is a placeholder for real maps.
}

GENERIC_MAP = {
    # Map known MLS columns to our normalized schema when needed.
}

NORMALIZED_COLUMNS = [
    "source","address","city","state","zip",
    "price","monthly_rent","units","year_built","sqft",
    "property_type","lat","lon","notes"
]
