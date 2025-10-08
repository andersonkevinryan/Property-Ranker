import numpy as np

def price_to_rent(price, monthly_rent):
    if price and monthly_rent and monthly_rent>0:
        return price/(monthly_rent*12.0)
    return np.nan

def cap_rate(price, monthly_rent, other_income_m, tax_y, ins_y, hoa_y, opex_ratio):
    annual_rent = (monthly_rent or 0)*12.0
    other_inc = (other_income_m or 0)*12.0
    opex = (annual_rent+other_inc)*(opex_ratio or 0.33)
    if price and price>0:
        return ((annual_rent+other_inc)-(opex+(tax_y or 0)+(ins_y or 0)+(hoa_y or 0)))/price
    return np.nan

def dscr(price, monthly_rent, other_income_m, tax_y, ins_y, hoa_y, opex_ratio, loan_constant):
    cr = cap_rate(price, monthly_rent, other_income_m, tax_y, ins_y, hoa_y, opex_ratio)
    noi = None
    if cr is not None and not np.isnan(cr) and price:
        noi = cr*price
    ads = (price or 0)*(loan_constant or 0.08)
    if ads>0 and noi is not None:
        return noi/ads
    return np.nan
