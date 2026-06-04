import json
import re
from pathlib import Path
import numpy as np
import pandas as pd

RAW_MENU_FILE = Path("data/raw/MEM_compstore_menus.csv")
RAW_RESTAURANT_FILE = Path("data/raw/MEM_compstore_restaurants.csv")
SEGMENTATION_FILE = Path("data/processed/segmentation_analysis.csv")
OUTPUT_FILE = Path("data/processed/menu_item_intelligence.csv")
EXCLUDED_OUTPUT_FILE = Path("data/processed/menu_item_excluded_non_food.csv")
SUMMARY_FILE = Path("output/menu_item_intelligence_summary.json")


EXCLUDE_TERMS = [
    "gift bag",
    "gift box",
    "gift certificate",
    "gift certficate",
    "gift card",
    "service charge",
    "gift",
    "voucher",
    "coupon",
    "bag",
    "merch",
    "discount",
    "membership",
    "subscription",
    "delivery fee",
    "service fee",
    "fee",
    "tax",
    "tip",
    "gratuity",
    "reservation",
    "booking fee",
]

EXACT_EXCLUDE_TERMS = {
    "tax",
    "tip",
    "tips",
    "gratuity",
}


TEXT_COLUMNS = [
    "menu_item",
    "description",
    "category",
    "menu_section",
    "ingredients",
    "cuisine",
]

CANONICAL_CATEGORY_RULES = {
    "Dumplings/Buns": [
        "bao",
        "banh bao",
        "dumpling",
        "dumplings",
        "gyoza",
        "har gow",
        "mandu",
        "momo",
        "pierogi",
        "pot sticker",
        "pot stickers",
        "potsticker",
        "potstickers",
        "pork bun",
        "bbq pork bun",
        "custard bun",
        "pan fried bun",
        "steamed bun",
        "siu mai",
        "shumai",
        "soup dumpling",
        "wonton",
        "xiao long bao",
        "xiu mai",
    ],
    "Sushi/Poke": ["sushi", "sashimi", "nigiri", "maki", "poke", "sushi roll"],
    "Pizza/Flatbreads": ["pizza", "flatbread"],
    "Tacos/Burritos": ["taco", "tacos", "burrito", "burritos", "quesadilla", "quesadillas"],
    "Burgers/Sandwiches": ["burger", "burgers", "sandwich", "sandwiches", "po'boy", "po boy", "philly"],
    "Pasta/Noodles": ["pasta", "noodle", "noodles", "ramen", "lo mein", "spaghetti"],
    "Wings/Chicken": ["wing", "wings", "tender", "tenders", "chicken"],
    "Seafood": ["shrimp", "fish", "crab", "catfish", "salmon", "oyster", "crawfish", "lobster"],
    "Salads": ["salad", "salads", "greens"],
    "Soups": ["soup", "soups", "chowder", "bisque"],
    "Breakfast": ["breakfast", "biscuit", "omelet", "omelette", "pancake", "waffle"],
    "Desserts": ["cake", "cookie", "brownie", "ice cream", "cheesecake", "dessert"],
    "Beverages": ["tea", "coffee", "soda", "juice", "smoothie", "lemonade", "beer", "drink"],
    "Sides": ["fries", "chips", "rice", "beans", "side"],
}

SOURCE_CATEGORY_ALIASES = {
    "appetizer": "Appetizers",
    "appetizers": "Appetizers",
    "beverage": "Beverages",
    "beverages": "Beverages",
    "coffee and tea": "Beverages",
    "dessert": "Desserts",
    "desserts": "Desserts",
    "entree": "Entrees",
    "entrees": "Entrees",
    "entr es": "Entrees",
    "entrées": "Entrees",
    "non-alcoholic beverages": "Beverages",
    "other": "Other",
    "pizza": "Pizza/Flatbreads",
    "pizzas": "Pizza/Flatbreads",
    "salad": "Salads",
    "salads": "Salads",
    "sandwich": "Burgers/Sandwiches",
    "sandwiches": "Burgers/Sandwiches",
    "sandwiches burgers": "Burgers/Sandwiches",
    "sandwiches & burgers": "Burgers/Sandwiches",
    "side": "Sides",
    "sides": "Sides",
    "soup": "Soups",
    "soups": "Soups",
    "soups salads": "Soups/Salads",
    "sushi": "Sushi/Poke",
}

CANONICAL_CATEGORY_PRIORITY = {
    category: priority
    for priority, category in enumerate(CANONICAL_CATEGORY_RULES)
}

KEYWORDS = {
    "cuisine_type": {
        "Korean": ["korean", "kimchi", "bulgogi", "gochujang", "bibimbap"],
        "Mexican": ["mexican", "taco", "burrito", "quesadilla", "nachos", "tortilla", "aguacate"],
        "Italian": ["italian", "pizza", "pasta", "alfredo", "lasagna", "parmesan"],
        "Japanese": ["japanese", "sushi", "ramen", "teriyaki", "tempura", "hibachi"],
        "Chinese": ["chinese", "lo mein", "fried rice", "dumpling", "szechuan", "soy sauce"],
        "Vietnamese": ["vietnamese", "banh", "pho", "bun bo", "vermicelli"],
        "Thai": ["thai", "pad thai", "curry", "basil", "satay"],
        "Indian": ["indian", "curry", "masala", "tikka", "naan", "biryani"],
        "Mediterranean": ["mediterranean", "gyro", "hummus", "falafel", "tzatziki"],
        "Cajun/Creole": ["cajun", "creole", "gumbo", "jambalaya", "po'boy", "po boy"],
        "American": ["burger", "fries", "wings", "sandwich", "bbq", "barbecue"],
    },
    "food_style": {
        "Dumplings/Buns": CANONICAL_CATEGORY_RULES["Dumplings/Buns"],
        "Burger/Sandwich": ["burger", "sandwich", "po'boy", "po boy", "philly"],
        "Bowl": ["bowl", "rice bowl", "protein bowl"],
        "Taco/Burrito": ["taco", "burrito", "quesadilla"],
        "Pizza": ["pizza", "flatbread"],
        "Pasta/Noodles": ["pasta", "noodle", "ramen", "lo mein", "spaghetti"],
        "Wings/Chicken": ["wing", "tender", "chicken"],
        "Seafood": ["shrimp", "fish", "crab", "catfish", "salmon", "oyster", "crawfish"],
        "Salad": ["salad", "greens"],
        "Dessert": ["cake", "cookie", "brownie", "ice cream", "cheesecake"],
        "Beverage": ["tea", "coffee", "soda", "juice", "smoothie", "lemonade", "beer"],
    },
    "flavor_profile": {
        "Spicy": ["spicy", "hot", "chili", "jalapeno", "sriracha", "buffalo", "cajun"],
        "Sweet": ["sweet", "honey", "caramel", "chocolate", "vanilla", "maple"],
        "Savory": ["savory", "garlic", "butter", "cheese", "gravy"],
        "Smoky": ["smoked", "smoky", "bbq", "barbecue"],
        "Fresh": ["fresh", "citrus", "lemon", "mint", "garden"],
    },
    "cooking_style": {
        "Fried": ["fried", "crispy", "tempura"],
        "Grilled": ["grilled", "chargrill", "charbroiled"],
        "Steamed": ["steamed"],
        "Baked": ["baked", "roasted"],
        "Boiled": ["boiled", "seafood boil"],
        "Raw/Cold": ["sushi", "poke", "ceviche", "salad"],
    },
    "dietary_category": {
        "Vegan": ["vegan"],
        "Vegetarian": ["vegetarian", "veggie", "plant based", "plant-based"],
        "Healthy": ["healthy", "grilled", "salad", "protein", "keto", "organic"],
        "Gluten Free": ["gluten free", "gluten-free"],
        "Comfort Food": ["fries", "burger", "pizza", "wings", "mac", "cheese", "fried"],
    },
    "food_trends": {
        "Fusion": ["fusion", "kimchi taco", "sushi burrito", "korean bbq", "birria"],
        "Protein Forward": ["protein", "grilled chicken", "salmon", "steak", "shrimp"],
        "Bowl Format": ["bowl", "rice bowl", "protein bowl", "poke"],
        "Premium": ["wagyu", "truffle", "lobster", "signature", "artisan"],
        "Plant Based": ["vegan", "plant based", "plant-based"],
        "Spicy Global": ["gochujang", "sriracha", "hot honey", "birria", "cajun"],
    },
    "target_audience_appeal": {
        "Youth Appeal": ["spicy", "loaded", "fusion", "boba", "taco", "burger", "wings"],
        "Family Friendly": ["kids", "combo", "family", "tender", "fries", "pizza"],
        "Health Conscious": ["salad", "grilled", "protein", "vegan", "organic"],
        "Premium Diners": ["lobster", "steak", "wagyu", "truffle", "signature"],
        "Late Night": ["wings", "fries", "burger", "pizza", "loaded", "nachos"],
    },
}


FEATURE_KEYWORDS = {
    "spicy": KEYWORDS["flavor_profile"]["Spicy"],
    "vegan": KEYWORDS["dietary_category"]["Vegan"],
    "healthy": KEYWORDS["dietary_category"]["Healthy"],
    "premium": KEYWORDS["food_trends"]["Premium"],
    "fusion": KEYWORDS["food_trends"]["Fusion"],
    "comfort_food": KEYWORDS["dietary_category"]["Comfort Food"],
    "trendy": (
        KEYWORDS["food_trends"]["Fusion"]
        + KEYWORDS["food_trends"]["Bowl Format"]
        + KEYWORDS["food_trends"]["Spicy Global"]
        + KEYWORDS["food_trends"]["Plant Based"]
    ),
    "family_friendly": KEYWORDS["target_audience_appeal"]["Family Friendly"],
    "late_night": KEYWORDS["target_audience_appeal"]["Late Night"],
}


PROTEIN_KEYWORDS = {
    "Chicken": ["chicken", "wing", "tender"],
    "Beef": ["beef", "steak", "burger", "brisket"],
    "Pork": ["pork", "bacon", "ham", "sausage"],
    "Seafood": ["shrimp", "fish", "crab", "salmon", "oyster", "crawfish", "catfish"],
    "Plant Based": ["vegan", "tofu", "plant based", "plant-based", "veggie"],
    "Egg": ["egg"],
}

TREND_WEIGHTS = {
    "fusion": 18,
    "healthy": 12,
    "premium": 10,
    "spicy": 10,
    "trendy": 16,
    "vegan": 10,
}

def clean_text(value):
    value = str(value).lower()
    value = re.sub(r"[^a-z0-9\s'\-/]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def matched_exclude_term(item_name):
    item = clean_text(item_name)
    for term in EXCLUDE_TERMS:
        if term in EXACT_EXCLUDE_TERMS:
            if item == term:
                return term
            continue

        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, item):
            return term
    return ""


def is_non_food_item(item_name):
    return bool(matched_exclude_term(item_name))


def exclude_non_food_items(df):
    df = df.copy()
    df["exclusion_reason"] = df["menu_item"].apply(matched_exclude_term)
    non_food_mask = df["exclusion_reason"].ne("")
    excluded_df = df.loc[non_food_mask].copy()
    food_df = df.loc[~non_food_mask].drop(columns=["exclusion_reason"]).copy()
    return food_df, excluded_df


def source_category_to_canonical(category):
    category = clean_text(category)
    return SOURCE_CATEGORY_ALIASES.get(category, category.title() if category else "Other")


def item_taxonomy_text(df):
    columns = [
        column
        for column in ["menu_item", "description", "menu_section", "ingredients", "cuisine"]
        if column in df.columns
    ]
    return (
        df[columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(clean_text)
    )


def choose_primary_category(categories):
    counts = categories.value_counts()
    max_count = counts.max()
    candidates = counts[counts.eq(max_count)].index.tolist()
    return min(
        candidates,
        key=lambda category: (
            CANONICAL_CATEGORY_PRIORITY.get(category, len(CANONICAL_CATEGORY_PRIORITY)),
            category,
        ),
    )


def normalize_taxonomy(df):
    df = df.copy()
    df["source_category"] = df["category"]

    taxonomy_text = item_taxonomy_text(df)
    rule_category = first_matching_labels(taxonomy_text, CANONICAL_CATEGORY_RULES, "")
    source_category = df["source_category"].map(source_category_to_canonical)
    df["category"] = rule_category.mask(rule_category.eq(""), source_category)

    item_key = df["menu_item"].map(clean_text)
    primary_category_by_item = df.groupby(item_key)["category"].transform(choose_primary_category)
    df["category"] = primary_category_by_item
    return df


def contains_any(series, words):
    pattern = r"\b(?:{})\b".format("|".join(re.escape(word) for word in words))
    return series.str.contains(pattern, regex=True, na=False).astype(int)


def first_matching_labels(series, groups, default="General"):
    labels = pd.Series(default, index=series.index, dtype="object")
    unmatched = pd.Series(True, index=series.index)

    for label, keywords in groups.items():
        matches = contains_any(series, keywords).eq(1) & unmatched
        labels.loc[matches] = label
        unmatched.loc[matches] = False

    return labels


def combined_matching_labels(series, groups, default="General"):
    output = pd.Series("", index=series.index, dtype="object")

    for label, keywords in groups.items():
        matches = contains_any(series, keywords).eq(1)
        output.loc[matches & output.ne("")] += ", "
        output.loc[matches] += label

    return output.mask(output.eq(""), default)


def price_tiers(prices):
    valid_prices = pd.to_numeric(prices, errors="coerce")
    low = valid_prices.quantile(0.33)
    high = valid_prices.quantile(0.67)
    return np.select(
        [valid_prices <= low, valid_prices >= high],
        ["value", "premium"],
        default="mid",
    )


def level_to_score(series):
    return series.map({
        "Low": 0.25,
        "Declining": 0.25,
        "Medium": 0.5,
        "Stable": 0.5,
        "Balanced Age Demand": 0.55,
        "High": 0.85,
        "Growing": 0.85,
        "Young Demand High": 0.9,
        "Senior Demand High": 0.7,
    }).fillna(0.5)


def build_menu_input(menu_df, restaurant_df):
    columns = [
        "restaurant_object_key",
        "menu_item_name",
        "standardized_category",
        "description",
        "price",
    ]
    optional_columns = [
        column
        for column in ["menu_section", "ingredients", "cuisine", "sales", "season"]
        if column in menu_df
    ]
    df = menu_df[columns + optional_columns].copy()
    df = df.merge(
        restaurant_df[
            [
                "restaurant_object_key",
                "restaurant_name",
                "zip_or_postal_code",
                "style",
                "cuisines",
                "restaurant_type",
                "rating_value",
                "review_count",
            ]
        ].drop_duplicates("restaurant_object_key"),
        on="restaurant_object_key",
        how="left",
    )
    return df.rename(columns={
        "restaurant_object_key": "restaurant_id",
        "menu_item_name": "menu_item",
        "standardized_category": "category",
        "cuisines": "restaurant_cuisines",
    })


def add_text_understanding(df):
    text_columns = [
        column
        for column in TEXT_COLUMNS
        if column in df.columns
    ]
    df["combined_text"] = (
        df[text_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(clean_text)
    )

    df["cuisine_type"] = first_matching_labels(
        df["combined_text"],
        KEYWORDS["cuisine_type"],
        "American/General",
    )
    df["food_style"] = first_matching_labels(
        df["combined_text"],
        KEYWORDS["food_style"],
        "General",
    )
    df["flavor_profile"] = combined_matching_labels(
        df["combined_text"],
        KEYWORDS["flavor_profile"],
    )
    df["cooking_style"] = combined_matching_labels(
        df["combined_text"],
        KEYWORDS["cooking_style"],
    )
    df["dietary_category"] = combined_matching_labels(
        df["combined_text"],
        KEYWORDS["dietary_category"],
    )
    df["food_trends"] = combined_matching_labels(
        df["combined_text"],
        KEYWORDS["food_trends"],
    )
    df["target_audience_appeal"] = combined_matching_labels(
        df["combined_text"],
        KEYWORDS["target_audience_appeal"],
    )
    return df


def add_features(df):
    for feature, keywords in FEATURE_KEYWORDS.items():
        df[feature] = contains_any(df["combined_text"], keywords)

    df["protein_type"] = first_matching_labels(
        df["combined_text"],
        PROTEIN_KEYWORDS,
        "Other/None",
    )
    df["price_tier"] = price_tiers(df["price"])
    return df


def add_market_scores(df, segmentation_df):
    market = segmentation_df.drop_duplicates("restaurant_object_key").rename(
        columns={"restaurant_object_key": "restaurant_id"}
    )
    df = df.merge(market, on="restaurant_id", how="left", suffixes=("", "_market"))

    young = level_to_score(df["Age Demand Level"])
    income = level_to_score(df["Income Level"])
    growth = level_to_score(df["Growth Level"])
    fast_food = level_to_score(df["Fast Food Level"])
    healthy = level_to_score(df["Healthy Level"])
    beverage = level_to_score(df["Beverage Level"])
    wings = level_to_score(df["Wings Level"])

    demand = (young * 0.25) + (income * 0.15) + (growth * 0.15)
    demand += np.where(df["healthy"].eq(1), healthy * 0.2, 0)
    demand += np.where(df["late_night"].eq(1) | df["comfort_food"].eq(1), fast_food * 0.15, 0)
    demand += np.where(df["food_style"].eq("Beverage"), beverage * 0.15, 0)
    demand += np.where(df["food_style"].eq("Wings/Chicken"), wings * 0.15, 0)
    df["demand_match_score"] = np.clip((demand / 0.9) * 100, 0, 100).round(1)
    df["demand_match_level"] = pd.cut(
        df["demand_match_score"],
        bins=[-1, 39, 69, 100],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    return df


def add_competition_scores(df):
    density = (
        df.groupby(["zip_or_postal_code", "food_style"])["restaurant_id"]
        .transform("nunique")
        .fillna(1)
    )
    category_density = (
        df.groupby(["zip_or_postal_code", "category"])["restaurant_id"]
        .transform("nunique")
        .fillna(1)
    )
    combined_density = (density * 0.7) + (category_density * 0.3)
    max_density = max(combined_density.max(), 1)

    df["competition_score"] = ((combined_density / max_density) * 100).round(1)
    df["competition_level"] = pd.cut(
        df["competition_score"],
        bins=[-1, 33, 66, 100],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    df["uniqueness_score"] = (100 - df["competition_score"]).round(1)
    df["market_gap_signal"] = np.select(
        [
            (df["demand_match_score"] >= 70) & (df["competition_score"] <= 35),
            df["competition_score"] >= 70,
        ],
        ["Opportunity Gap", "Oversaturated"],
        default="Balanced",
    )
    return df


def add_trend_and_performance(df):
    trend_score = pd.Series(35, index=df.index, dtype="float")
    for feature, weight in TREND_WEIGHTS.items():
        trend_score += df[feature] * weight
    trend_score += np.where(df["food_style"].isin(["Bowl", "Taco/Burrito"]), 8, 0)
    df["trend_score"] = np.clip(trend_score, 0, 100).round(1)

    prices = pd.to_numeric(df["price"], errors="coerce")
    price_score = np.select(
        [df["price_tier"] == "premium", df["price_tier"] == "mid"],
        [80, 60],
        default=45,
    )
    df["profitability_score"] = np.where(prices <= 0, 50, price_score).round(1)
    df["seasonality_score"] = np.where(
        df.get("season", pd.Series("", index=df.index)).fillna("").astype(str).str.len() > 0,
        75,
        55,
    )

    if "sales" in df.columns:
        sales = pd.to_numeric(df["sales"], errors="coerce")
        max_sales = max(sales.max(skipna=True), 1)
        df["sales_performance_score"] = ((sales.fillna(sales.median()) / max_sales) * 100).round(1)
    else:
        df["sales_performance_score"] = 50.0

    df["performance_score"] = (
        df["sales_performance_score"] * 0.2
        + df["demand_match_score"] * 0.25
        + (100 - df["competition_score"]) * 0.15
        + df["trend_score"] * 0.15
        + df["uniqueness_score"] * 0.1
        + df["profitability_score"] * 0.1
        + df["seasonality_score"] * 0.05
    ).round(1)

    df["performance_level"] = pd.cut(
        df["performance_score"],
        bins=[-1, 44, 69, 100],
        labels=["Weak", "Moderate", "Strong"],
    ).astype(str)
    return df


def add_recommendations(df):
    generic_item = (
        df["food_style"].eq("General")
        & df["flavor_profile"].eq("General")
        & df["food_trends"].eq("General")
    )

    df["recommended_action"] = np.select(
        [
            (df["performance_score"] < 42) & (df["competition_score"] >= 60),
            (df["performance_score"] >= 75) & (df["demand_match_score"] >= 70),
            (df["market_gap_signal"] == "Opportunity Gap") & (df["trend_score"] >= 60),
            (df["trend_score"] >= 70) & (df["performance_score"] < 65),
            (df["competition_score"] >= 70) & (df["demand_match_score"] >= 55),
            df["seasonality_score"] >= 70,
            df["performance_score"] < 50,
            generic_item & df["performance_score"].between(45, 60),
            df["performance_score"] >= 55,
        ],
        [
            "Remove",
            "Promote",
            "Add Variant",
            "Reposition",
            "Refresh Recipe",
            "Seasonal Special",
            "Refresh Recipe",
            "Rename",
            "Keep",
        ],
        default="Keep",
    )
    return df


def save_outputs(df, excluded_df=None):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)

    output_columns = [
        "restaurant_id",
        "restaurant_name",
        "zip_or_postal_code",
        "menu_item",
        "category",
        "description",
        "price",
        "cuisine_type",
        "food_style",
        "flavor_profile",
        "cooking_style",
        "dietary_category",
        "food_trends",
        "target_audience_appeal",
        "spicy",
        "vegan",
        "healthy",
        "premium",
        "fusion",
        "comfort_food",
        "trendy",
        "family_friendly",
        "late_night",
        "protein_type",
        "price_tier",
        "market_segment",
        "Age Demand Level",
        "Income Level",
        "Competition Level",
        "demand_match_score",
        "demand_match_level",
        "competition_score",
        "competition_level",
        "market_gap_signal",
        "trend_score",
        "sales_performance_score",
        "uniqueness_score",
        "profitability_score",
        "seasonality_score",
        "performance_score",
        "performance_level",
        "recommended_action",
    ]
    existing_columns = [column for column in output_columns if column in df.columns]

    output_path = OUTPUT_FILE
    try:
        df[existing_columns].to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        output_path = OUTPUT_FILE.with_suffix(".csv.tmp")
        df[existing_columns].to_csv(output_path, index=False)
        print(
            f"Could not replace {OUTPUT_FILE}. Close the file if it is open, "
            f"then rerun the script. Latest output is available at {output_path}."
        )

    summary = {
        "total_menu_rows": int(len(df)),
        "excluded_non_food_rows": int(len(excluded_df)) if excluded_df is not None else 0,
        "restaurants_analyzed": int(df["restaurant_id"].nunique()),
        "average_performance_score": round(float(df["performance_score"].mean()), 1),
        "action_counts": df["recommended_action"].value_counts().to_dict(),
        "top_items": df.nlargest(10, "performance_score")[
            ["restaurant_name", "menu_item", "performance_score", "recommended_action"]
        ].to_dict(orient="records"),
        "weak_items": df.nsmallest(10, "performance_score")[
            ["restaurant_name", "menu_item", "performance_score", "recommended_action"]
        ].to_dict(orient="records"),
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    return output_path, SUMMARY_FILE


def save_excluded_items(excluded_df):
    if excluded_df.empty:
        return None

    EXCLUDED_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "restaurant_id",
        "restaurant_name",
        "menu_item",
        "category",
        "description",
        "price",
        "exclusion_reason",
    ]
    existing_columns = [column for column in columns if column in excluded_df.columns]

    try:
        excluded_df[existing_columns].to_csv(EXCLUDED_OUTPUT_FILE, index=False)
        return EXCLUDED_OUTPUT_FILE
    except PermissionError:
        output_path = EXCLUDED_OUTPUT_FILE.with_suffix(".csv.tmp")
        excluded_df[existing_columns].to_csv(output_path, index=False)
        print(
            f"Could not replace {EXCLUDED_OUTPUT_FILE}. Close the file if it is open, "
            f"then rerun the script. Latest excluded-item audit is available at {output_path}."
        )
        return output_path


def run_menu_item_intelligence():
    menu_df = pd.read_csv(RAW_MENU_FILE)
    restaurant_df = pd.read_csv(RAW_RESTAURANT_FILE)

    if SEGMENTATION_FILE.exists():
        segmentation_df = pd.read_csv(SEGMENTATION_FILE)
    else:
        segmentation_df = restaurant_df[["restaurant_object_key"]].copy()

    df = build_menu_input(menu_df, restaurant_df)
    df, excluded_df = exclude_non_food_items(df)
    excluded_file = save_excluded_items(excluded_df)
    df = normalize_taxonomy(df)
    df = add_text_understanding(df)
    df = add_features(df)
    df = add_market_scores(df, segmentation_df)
    df = add_competition_scores(df)
    df = add_trend_and_performance(df)
    df = add_recommendations(df)

    output_file, summary_file = save_outputs(df, excluded_df)
    print("Phase 1 menu item intelligence complete.")
    print(f"Internal analytics file: {output_file}")
    if excluded_file is not None:
        print(f"Excluded POS/non-food audit file: {excluded_file}")
    print(f"Summary file: {summary_file}")

    return df


if __name__ == "__main__":
    run_menu_item_intelligence()
