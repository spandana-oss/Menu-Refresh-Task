import pandas as pd

def restaurants():
    df_restaurant = pd.read_csv("data/raw/MEM_compstore_restaurants.csv")

    # Remove duplicates
    df = df_restaurant.drop_duplicates(subset=['restaurant_object_key']).copy()

    # Clean ZIP
    df['zip_or_postal_code'] = df['zip_or_postal_code'].astype(str).str.zfill(5)
    df = df[df['zip_or_postal_code'].str.match(r'^\d{5}$')].copy()

    # Create ZCTA
    df['ZCTA'] = df['zip_or_postal_code']
    return df



