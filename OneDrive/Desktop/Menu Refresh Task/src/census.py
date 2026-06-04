import requests
import pandas as pd
import time
import numpy as np
from dotenv import load_dotenv
import os


# Load .env file
load_dotenv()

# Read API key from environment
API_KEY = os.getenv("API_KEY")


def _zcta_column(df):
    return "zip code tabulation area"


def safe_request(url, params, retries=3, timeout=30):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)

            if response.status_code == 200:
                return response.json()

            else:
                print(f"API error: {response.status_code} | {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed: {e}")

        time.sleep(2 ** attempt)  # exponential backoff

    raise Exception("All retries failed. API unreachable.")

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def load_cache(filename):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def save_cache(df, filename):
    path = os.path.join(CACHE_DIR, filename)
    df.to_csv(path, index=False)


def fetch_cbp():
    cache_file = "cbp.csv"

    # 🔹 Try cache first
    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded CBP from cache")
        return cached
    
    url = "https://api.census.gov/data/2022/cbp"

    params = {
        "get": "ESTAB,EMP,NAICS2017",
        "for": "county:*",
        "in": "state:*",
        "NAICS2017": "7225",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(data[1:], columns=data[0])

    df['ESTAB'] = pd.to_numeric(df['ESTAB'], errors='coerce')
    df['EMP'] = pd.to_numeric(df['EMP'], errors='coerce')

    df['FIPS'] = df['state'] + df['county']

    result = df[['FIPS', 'ESTAB', 'EMP']]
    save_cache(result, cache_file)

    return result



def fetch_population():
    cache_file = "population.csv"

    # 🔹 Try cache first
    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded population from cache")
        return cached

    url = "https://api.census.gov/data/2022/acs/acs5"

    params = {
        "get": "B01003_001E",
        "for": "zip code tabulation area:*",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(data[1:], columns=data[0])

    df = df.rename(columns={"B01003_001E": "POP"})

    df['POP'] = pd.to_numeric(df['POP'])

    df['ZCTA'] = df[_zcta_column(df)].astype(str).str.zfill(5)

    result = df[['ZCTA', 'POP']]
    save_cache(result, cache_file)

    return result

def fetch_income():
    cache_file = "income.csv"

    # 🔹 Try cache first
    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded income from cache")
        return cached
    
    url = "https://api.census.gov/data/2022/acs/acs5"

    params = {
        "get": "B19013_001E",
        "for": "zip code tabulation area:*",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(data[1:], columns=data[0])

    df = df.rename(columns={
        "B19013_001E": "MEDIAN_INCOME"
    })

    df['MEDIAN_INCOME'] = pd.to_numeric(
        df['MEDIAN_INCOME'],
        errors='coerce'
    )

    df['ZCTA'] = df[_zcta_column(df)].astype(str).str.zfill(5)

    result = df[['ZCTA', 'MEDIAN_INCOME']]
    save_cache(result, cache_file)

    return result


def fetch_household_size():
    cache_file = "household_size.csv"

    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded household_size from cache")
        return cached

    url = "https://api.census.gov/data/2022/acs/acs5"

    params = {
        "get": "B25010_001E",
        "for": "zip code tabulation area:*",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(
        data[1:],
        columns=data[0]
    )

    df = df.rename(columns={
        "B25010_001E": "AVG_HOUSEHOLD_SIZE"
    })

    df["AVG_HOUSEHOLD_SIZE"] = pd.to_numeric(
        df["AVG_HOUSEHOLD_SIZE"],
        errors="coerce"
    )

    df["ZCTA"] = (
        df[_zcta_column(df)]
        .astype(str)
        .str.zfill(5)
    )

    result = df[
        ["ZCTA", "AVG_HOUSEHOLD_SIZE"]
    ]
    save_cache(result, cache_file)

    return result


def fetch_ethnicity():
    cache_file = "ethnicity.csv"

    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded ethnicity from cache")
        return cached

    url = "https://api.census.gov/data/2022/acs/acs5"

    params = {
        "get": (
            "B02001_002E,"
            "B02001_003E,"
            "B02001_005E,"
            "B03003_003E"
        ),
        "for": "zip code tabulation area:*",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(
        data[1:],
        columns=data[0]
    )

    df = df.rename(columns={
        "B02001_002E": "WHITE_POP",
        "B02001_003E": "BLACK_POP",
        "B02001_005E": "ASIAN_POP",
        "B03003_003E": "HISPANIC_POP"
    })

    cols = [
        "WHITE_POP",
        "BLACK_POP",
        "ASIAN_POP",
        "HISPANIC_POP"
    ]

    for col in cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df["ZCTA"] = (
        df[_zcta_column(df)]
        .astype(str)
        .str.zfill(5)
    )

    result = df[
        ["ZCTA"] + cols
    ]
    save_cache(result, cache_file)

    return result


def fetch_median_gross_rent():
    cache_file = "median_gross_rent.csv"

    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded median_gross_rent from cache")
        return cached

    url = "https://api.census.gov/data/2022/acs/acs5"

    params = {
        "get": "B25064_001E",
        "for": "zip code tabulation area:*",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(
        data[1:],
        columns=data[0]
    )

    df = df.rename(columns={
        "B25064_001E": "MEDIAN_GROSS_RENT"
    })

    df["MEDIAN_GROSS_RENT"] = pd.to_numeric(
        df["MEDIAN_GROSS_RENT"],
        errors="coerce"
    )

    df["ZCTA"] = (
        df[_zcta_column(df)]
        .astype(str)
        .str.zfill(5)
    )

    result = df[
        ["ZCTA", "MEDIAN_GROSS_RENT"]
    ]
    save_cache(result, cache_file)

    return result


def fetch_age_distribution():
    cache_file = "age_distribution.csv"

    # 🔹 Try cache first
    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded age_distribution from cache")
        return cached

    url = "https://api.census.gov/data/2022/acs/acs5/subject"

    params = {
        "get": (
            "S0101_C01_019E,"  # 18-24
            "S0101_C01_020E,"  # 25-34
            "S0101_C01_021E,"  # 35-44
            "S0101_C01_023E,"  # 55-64
            "S0101_C01_024E"   # 65+
        ),
        "for": "zip code tabulation area:*",
        "key": API_KEY
    }

    data = safe_request(url, params)

    df = pd.DataFrame(data[1:], columns=data[0])

    df = df.rename(columns={
        "S0101_C01_019E": "AGE_18_24",
        "S0101_C01_020E": "AGE_25_34",
        "S0101_C01_021E": "AGE_35_44",
        "S0101_C01_023E": "AGE_55_64",
        "S0101_C01_024E": "AGE_65_PLUS"
    })

    age_cols = [
        'AGE_18_24',
        'AGE_25_34',
        'AGE_35_44',
        'AGE_55_64',
        'AGE_65_PLUS'
    ]

    for col in age_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['ZCTA'] = df[_zcta_column(df)].astype(str).str.zfill(5)

    result = df[['ZCTA'] + age_cols]
    save_cache(result, cache_file)

    return result


def fetch_population_growth():
    cache_file = "population_growth.csv"

    # 🔹 Try cache first
    cached = load_cache(cache_file)
    if cached is not None:
        print("Loaded population growth from cache")
        return cached

    try:
        # ---------------- CURRENT (2022) ----------------
        url_2022 = "https://api.census.gov/data/2022/acs/acs5"
        params_2022 = {
            "get": "B01003_001E",
            "for": "zip code tabulation area:*",
            "key": API_KEY
        }

        data_2022 = safe_request(url_2022, params_2022)

        df_2022 = pd.DataFrame(data_2022[1:], columns=data_2022[0])
        df_2022 = df_2022.rename(columns={"B01003_001E": "POP_2022"})

        # ---------------- OLD (2017) ----------------
        url_2017 = "https://api.census.gov/data/2017/acs/acs5"
        params_2017 = {
            "get": "B01003_001E",
            "for": "zip code tabulation area:*",
            "key": API_KEY
        }

        data_2017 = safe_request(url_2017, params_2017)

        df_2017 = pd.DataFrame(data_2017[1:], columns=data_2017[0])
        df_2017 = df_2017.rename(columns={"B01003_001E": "POP_2017"})

        # ---------------- FORMAT ----------------
        ZCTA_COL = "zip code tabulation area"

        for df in [df_2022, df_2017]:
            df["ZCTA"] = df[ZCTA_COL].astype(str).str.zfill(5)

        # ---------------- MERGE ----------------
        df = df_2022.merge(
            df_2017[["ZCTA", "POP_2017"]],
            on="ZCTA",
            how="left"
        )

        df["POP_2022"] = pd.to_numeric(df["POP_2022"], errors="coerce")
        df["POP_2017"] = pd.to_numeric(df["POP_2017"], errors="coerce")

        # ---------------- SAFE GROWTH ----------------
        df["population_growth_rate"] = np.where(
            df["POP_2017"] > 0,
            ((df["POP_2022"] - df["POP_2017"]) / df["POP_2017"]) * 100,
            np.nan
        )

        result = df[["ZCTA", "population_growth_rate"]]

        # 🔹 Save cache
        save_cache(result, cache_file)

        return result

    except Exception as e:
        print("API failed for population growth, trying cache...")

        cached = load_cache(cache_file)
        if cached is not None:
            return cached

        raise Exception("No cache available and API failed.") from e

