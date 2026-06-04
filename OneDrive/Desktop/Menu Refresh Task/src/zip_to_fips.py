import numpy as np
import pandas as pd


def get_zip_to_fips():

    # -----------------------------------------
    # LOAD COUNTY/ZCTA MAPPING
    # -----------------------------------------

    df = pd.read_csv(
        "data/raw/county_zcta.csv",
        dtype=str
    )

    df.columns = df.columns.str.lower()

    # -----------------------------------------
    # CLEAN ZIP/FIPS
    # -----------------------------------------

    df['zcta'] = (
        df['zcta']
        .astype(str)
        .str.zfill(5)
    )

    df['state'] = (
        df['state']
        .astype(str)
        .str.zfill(2)
    )

    df['county'] = (
        df['county']
        .astype(str)
        .str.zfill(3)
    )

    # FIPS
    df['FIPS'] = df['state'] + df['county']

    # -----------------------------------------
    # LOAD ZIP GEOGRAPHY
    # -----------------------------------------

    geo = pd.read_csv(
        "data/raw/zip_geography.csv",
        dtype=str
    )

    geo.columns = geo.columns.str.strip().str.lower()

    geo = geo.rename(
        columns={
            "zip": "ZCTA",
            "city": "CITY",
            "state_id": "STATE",
            "county_name": "COUNTY",
            "lat": "LAT",
            "lng": "LNG",
            "density": "POP_DENSITY"
        }
    )

    geo["ZCTA"] = (
        geo["ZCTA"]
        .astype(str)
        .str.zfill(5)
    )

    # -----------------------------------------
    # MERGE GEOGRAPHY
    # -----------------------------------------

    df = df.merge(
        geo,
        left_on="zcta",
        right_on="ZCTA",
        how="left"
    )

    if "zcta_x" in df.columns:
        df = df.rename(columns={"zcta_x": "zcta"})

    # -----------------------------------------
    # NUMERIC CONVERSIONS
    # -----------------------------------------

    numeric_cols = [
        "LAT",
        "LNG",
        "POP_DENSITY"
    ]

    for col in numeric_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # -----------------------------------------
    # URBAN / SUBURBAN / RURAL
    # -----------------------------------------

    conditions = [

        df["POP_DENSITY"] >= 3000,

        (df["POP_DENSITY"] >= 1000) &
        (df["POP_DENSITY"] < 3000),

        df["POP_DENSITY"] < 1000
    ]

    values = [
        "URBAN",
        "SUBURBAN",
        "RURAL"
    ]

    df["AREA_TYPE"] = np.select(
        conditions,
        values,
        default="UNKNOWN"
    )

    # -----------------------------------------
    # RETURN FINAL
    # -----------------------------------------

    return df[
        [
            "zcta",
            "FIPS",
            "CITY",
            "STATE",
            "COUNTY",
            "LAT",
            "LNG",
            "POP_DENSITY",
            "AREA_TYPE"
        ]
    ]


def load_zip_geography():
    geo = pd.read_csv(
        "data/raw/zip_geography.csv",
        dtype=str
    )

    geo.columns = geo.columns.str.strip().str.lower()
    geo = geo.rename(
        columns={
            "zip": "ZCTA",
            "zcta": "ZCTA_FLAG",
            "city": "CITY",
            "state_id": "STATE",
            "county_name": "COUNTY",
            "lat": "LAT",
            "lng": "LNG",
            "density": "POP_DENSITY",
            "land_area_sqkm": "LAND_AREA_SQKM"
        }
    )

    geo["ZCTA"] = geo["ZCTA"].astype(str).str.zfill(5)

    return geo


def add_population_density(geo_df, population_df):
    population_df = population_df.copy()
    population_df["ZCTA"] = population_df["ZCTA"].astype(str).str.zfill(5)

    df = geo_df.merge(
        population_df,
        on="ZCTA",
        how="left"
    )

    df["POP"] = pd.to_numeric(df["POP"], errors="coerce")

    if "POP_DENSITY" in df.columns:
        df["POP_DENSITY"] = pd.to_numeric(
            df["POP_DENSITY"],
            errors="coerce"
        )
    elif "LAND_AREA_SQKM" in df.columns:
        land_area = pd.to_numeric(
            df["LAND_AREA_SQKM"],
            errors="coerce"
        )
        df["POP_DENSITY"] = df["POP"] / land_area.replace(0, np.nan)
    else:
        df["POP_DENSITY"] = np.nan

    return df


def classify_area_type(df):
    conditions = [
        df["POP_DENSITY"] >= 3000,
        (df["POP_DENSITY"] >= 1000) & (df["POP_DENSITY"] < 3000),
        df["POP_DENSITY"] < 1000
    ]

    values = [
        "URBAN",
        "SUBURBAN",
        "RURAL"
    ]

    df["AREA_TYPE"] = np.select(
        conditions,
        values,
        default="UNKNOWN"
    )

    return df


def add_competitor_density(df, restaurants_df):
    restaurants_df = restaurants_df.copy()
    restaurants_df["ZCTA"] = restaurants_df["ZCTA"].astype(str).str.zfill(5)

    restaurant_counts = (
        restaurants_df
        .groupby("ZCTA")
        .size()
        .reset_index(name="RESTAURANT_COUNT")
    )

    df = df.merge(
        restaurant_counts,
        on="ZCTA",
        how="left"
    )

    df["RESTAURANT_COUNT"] = pd.to_numeric(
        df["RESTAURANT_COUNT"],
        errors="coerce"
    ).fillna(0)

    df["COMPETITOR_DENSITY"] = (
        df["RESTAURANT_COUNT"] /
        df["POP"].replace(0, np.nan)
    ) * 1000

    return df


def build_geographic_intelligence(
    population_df,
    restaurants_df
):
    geo = load_zip_geography()
    geo = add_population_density(geo, population_df)
    geo = classify_area_type(geo)
    geo = add_competitor_density(geo, restaurants_df)

    geo = geo[
        [
            "ZCTA",
            "CITY",
            "STATE",
            "COUNTY",
            "LAT",
            "LNG",
            "POP",
            "POP_DENSITY",
            "AREA_TYPE",
            "RESTAURANT_COUNT",
            "COMPETITOR_DENSITY"
        ]
    ]

    return geo
