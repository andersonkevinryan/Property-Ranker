import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("/tmp/investor_steroids.duckdb")

def get_con():
    return duckdb.connect(DB_PATH.as_posix())

def init_db():
    con = get_con()
    con.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            source VARCHAR,
            address VARCHAR,
            city VARCHAR,
            state VARCHAR,
            zip VARCHAR,
            price DOUBLE,
            monthly_rent DOUBLE,
            units INTEGER,
            year_built INTEGER,
            sqft DOUBLE,
            property_type VARCHAR,
            lat DOUBLE,
            lon DOUBLE,
            notes VARCHAR
        );
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS saved_criteria (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            name VARCHAR,
            criteria_json VARCHAR
        );
    """)
    con.close()

def insert_listings(df: pd.DataFrame):
    con = get_con()
    con.register("df", df)
    con.execute("""
        INSERT INTO listings
        SELECT source, address, city, state, zip, price, monthly_rent, units, year_built, sqft, property_type, lat, lon, notes
        FROM df
    """)
    con.close()

def fetch_listings():
    con = get_con()
    df = con.execute("SELECT * FROM listings").fetchdf()
    con.close()
    return df

def fetch_listings_filtered(sql_where: str):
    con = get_con()
    df = con.execute(f"SELECT * FROM listings WHERE {sql_where}").fetchdf()
    con.close()
    return df

def save_criteria(name: str, criteria_json: str):
    con = get_con()
    con.execute("INSERT INTO saved_criteria (name, criteria_json) VALUES (?, ?)", [name, criteria_json])
    con.close()

def load_criteria():
    con = get_con()
    df = con.execute("SELECT * FROM saved_criteria ORDER BY id DESC").fetchdf()
    con.close()
    return df
