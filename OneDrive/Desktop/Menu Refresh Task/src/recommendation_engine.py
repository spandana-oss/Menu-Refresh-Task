from pathlib import Path

import numpy as np
import pandas as pd

INPUT_FILE = Path("data/processed/menu_item_intelligence.csv")
OUTPUT_FILE = Path("data/processed/menu_item_recommendations.csv")

RECOMMENDATION_TYPES = [
    "KEEP",
    "PROMOTE",
    "REMOVE",
    "REFRESH_RECIPE",
    "REPOSITION",
    "ADD_NEW_ITEM",
    "SEASONAL_SPECIAL",
    "EXPAND_CATEGORY",
    "PRICE_OPTIMIZATION",
]

OPPORTUNITY_CATEGORIES = {
    "Beverages",
    "Breakfast",
    "Burgers/Sandwiches",
    "Desserts",
    "Dumplings/Buns",
    "Pasta/Noodles",
    "Pizza/Flatbreads",
    "Salads",
    "Seafood",
    "Soups",
    "Sushi/Poke",
    "Tacos/Burritos",
    "Wings/Chicken",
}

NUMERIC_COLUMNS = [
    "price",
    "spicy",
    "vegan",
    "healthy",
    "premium",
    "fusion",
    "comfort_food",
    "trendy",
    "family_friendly",
    "late_night",
    "demand_match_score",
    "competition_score",
    "trend_score",
    "sales_performance_score",
    "uniqueness_score",
    "profitability_score",
    "seasonality_score",
    "performance_score",
]

TEXT_COLUMNS = [
    "restaurant_name",
    "zip_or_postal_code",
    "category",
    "description",
    "cuisine_type",
    "food_style",
    "flavor_profile",
    "cooking_style",
    "dietary_category",
    "food_trends",
    "target_audience_appeal",
    "protein_type",
    "price_tier",
    "market_segment",
    "Age Demand Level",
    "Income Level",
    "Competition Level",
    "demand_match_level",
    "competition_level",
    "market_gap_signal",
    "performance_level",
    "recommended_action",
]

CORE_ITEM_TYPES = [
    "KEEP",
    "PROMOTE",
    "REMOVE",
    "REFRESH_RECIPE",
    "REPOSITION",
    "SEASONAL_SPECIAL",
]


def _first_non_empty(values):
    values = values.dropna().astype(str)
    values = values[values.str.strip().ne("")]
    if values.empty:
        return ""
    return values.iloc[0]


def _score(value, low, high):
    if high <= low:
        return 0.0
    return float(np.clip((value - low) / (high - low), 0, 1))


def _score_series(values, low, high):
    if high <= low:
        return pd.Series(0.0, index=values.index)
    return ((values - low) / (high - low)).clip(0, 1)


def load_scored_items(input_file=INPUT_FILE):
    return pd.read_csv(input_file)


def dedupe_items(df):
    keys = ["restaurant_id", "menu_item"]
    numeric_columns = [column for column in NUMERIC_COLUMNS if column in df.columns]
    text_columns = [column for column in TEXT_COLUMNS if column in df.columns]

    numeric_df = (
        df.groupby(keys, as_index=False)[numeric_columns]
        .mean()
    )
    text_df = (
        df[keys + text_columns]
        .drop_duplicates(keys)
        .copy()
    )
    item_df = text_df.merge(numeric_df, on=keys, how="left")

    if "recommended_action" in item_df.columns:
        item_df = item_df.rename(columns={"recommended_action": "backend_recommended_action"})

    return item_df


def add_benchmarks(df):
    df = df.copy()
    category_group = df.groupby("category")
    restaurant_category_group = df.groupby(["restaurant_id", "category"])

    df["category_avg_performance"] = category_group["performance_score"].transform("mean")
    df["category_avg_demand"] = category_group["demand_match_score"].transform("mean")
    df["category_avg_trend"] = category_group["trend_score"].transform("mean")
    df["category_avg_competition"] = category_group["competition_score"].transform("mean")
    df["category_avg_uniqueness"] = category_group["uniqueness_score"].transform("mean")
    df["category_median_price"] = category_group["price"].transform("median")
    df["category_price_percentile"] = category_group["price"].rank(pct=True)

    df["restaurant_category_item_count"] = restaurant_category_group["menu_item"].transform("count")
    df["restaurant_category_performance"] = restaurant_category_group["performance_score"].transform("mean")
    df["restaurant_category_demand"] = restaurant_category_group["demand_match_score"].transform("mean")
    df["restaurant_avg_performance"] = df.groupby("restaurant_id")["performance_score"].transform("mean")

    df["performance_vs_restaurant"] = df["performance_score"] - df["restaurant_avg_performance"]
    df["performance_vs_category"] = df["performance_score"] - df["category_avg_performance"]
    return df


def prepare_items(df):
    return add_benchmarks(dedupe_items(df))


def _core_recommendation(row):
    performance = row["performance_score"]
    demand = row["demand_match_score"]
    trend = row["trend_score"]
    competition = row["competition_score"]
    uniqueness = row["uniqueness_score"]
    category_demand = row["category_avg_demand"]
    category_performance = row["restaurant_category_performance"]
    generic = (
        row.get("food_style") == "General"
        and row.get("flavor_profile") == "General"
        and row.get("food_trends") == "General"
    )

    if performance <= 44 and competition >= 58 and uniqueness <= 45:
        return "REMOVE"

    if demand <= 38 and performance <= 45 and competition >= 50:
        return "REMOVE"

    if (
        performance >= 58
        and demand >= 52
        and (trend >= 47 or row.get("market_gap_signal") == "Opportunity Gap" or uniqueness >= 70)
    ):
        return "PROMOTE"

    if trend >= 55 and demand >= 48 and performance >= 52:
        return "PROMOTE"

    if trend >= 55 and performance < 56 and demand >= 45:
        return "REPOSITION"

    if generic and performance >= 48 and demand >= 45:
        return "REPOSITION"

    if category_demand >= 48 and performance <= 52 and category_performance >= 48:
        return "REFRESH_RECIPE"

    if demand >= 50 and performance <= 52 and competition >= 45:
        return "REFRESH_RECIPE"

    if performance >= 53 and uniqueness >= 50:
        return "KEEP"

    if performance >= row["restaurant_avg_performance"] and demand >= 42:
        return "KEEP"

    return "REFRESH_RECIPE"


def _price_optimization_score(row):
    percentile = row["category_price_percentile"]
    performance = row["performance_score"]
    category_performance = row["category_avg_performance"]
    category_price = row["category_median_price"]
    price = row["price"]

    high_price_underperforming = percentile >= 0.9 and performance < category_performance
    low_price_strong_item = percentile <= 0.1 and performance >= category_performance + 4
    large_price_gap = category_price > 0 and abs(price - category_price) / category_price >= 0.45

    if high_price_underperforming or low_price_strong_item or large_price_gap:
        return (
            _score(abs(percentile - 0.5), 0.35, 0.5) * 45
            + _score(abs(performance - category_performance), 2, 12) * 35
            + _score(abs(price - category_price), 2, 15) * 20
        )
    return 0.0


def _seasonal_special_score(row):
    seasonal_profile = (
        row.get("spicy", 0)
        + row.get("healthy", 0)
        + row.get("premium", 0)
        + row.get("fusion", 0)
        + row.get("trendy", 0)
        + row.get("family_friendly", 0)
        + row.get("late_night", 0)
    )
    if row["trend_score"] >= 47 and row["performance_score"] >= 50 and seasonal_profile > 0:
        return (
            _score(row["trend_score"], 45, 75) * 45
            + _score(row["demand_match_score"], 45, 70) * 30
            + min(seasonal_profile, 3) * 8
        )
    return 0.0


def _recommendation_strength(row, recommendation_type):
    performance = row["performance_score"]
    demand = row["demand_match_score"]
    trend = row["trend_score"]
    competition = row["competition_score"]
    uniqueness = row["uniqueness_score"]

    if recommendation_type == "KEEP":
        return (
            _score(performance, 50, 65) * 45
            + _score(demand, 42, 65) * 25
            + _score(uniqueness, 45, 85) * 30
        )
    if recommendation_type == "PROMOTE":
        return (
            _score(performance, 52, 68) * 30
            + _score(demand, 48, 70) * 30
            + _score(trend, 45, 75) * 25
            + _score(uniqueness, 55, 90) * 15
        )
    if recommendation_type == "REMOVE":
        return (
            _score(45 - performance, 0, 15) * 40
            + _score(competition, 50, 85) * 35
            + _score(50 - uniqueness, 0, 30) * 25
        )
    if recommendation_type == "REFRESH_RECIPE":
        return (
            _score(demand, 45, 65) * 35
            + _score(55 - performance, 0, 15) * 35
            + _score(competition, 40, 75) * 30
        )
    if recommendation_type == "REPOSITION":
        return (
            _score(trend, 45, 70) * 40
            + _score(demand, 45, 65) * 30
            + _score(60 - performance, 0, 15) * 30
        )
    if recommendation_type == "SEASONAL_SPECIAL":
        return _seasonal_special_score(row)
    if recommendation_type == "PRICE_OPTIMIZATION":
        return _price_optimization_score(row)
    return 0.0


def _core_recommendation_series(df):
    generic = (
        df["food_style"].eq("General")
        & df["flavor_profile"].eq("General")
        & df["food_trends"].eq("General")
    )
    conditions = [
        (df["performance_score"] <= 44)
        & (df["competition_score"] >= 58)
        & (df["uniqueness_score"] <= 45),
        (df["demand_match_score"] <= 38)
        & (df["performance_score"] <= 45)
        & (df["competition_score"] >= 50),
        (df["performance_score"] >= 58)
        & (df["demand_match_score"] >= 52)
        & (
            (df["trend_score"] >= 47)
            | df["market_gap_signal"].eq("Opportunity Gap")
            | (df["uniqueness_score"] >= 70)
        ),
        (df["trend_score"] >= 55)
        & (df["demand_match_score"] >= 48)
        & (df["performance_score"] >= 52),
        (df["trend_score"] >= 55)
        & (df["performance_score"] < 56)
        & (df["demand_match_score"] >= 45),
        generic & (df["performance_score"] >= 48) & (df["demand_match_score"] >= 45),
        (df["category_avg_demand"] >= 48)
        & (df["performance_score"] <= 52)
        & (df["restaurant_category_performance"] >= 48),
        (df["demand_match_score"] >= 50)
        & (df["performance_score"] <= 52)
        & (df["competition_score"] >= 45),
        (df["performance_score"] >= 53) & (df["uniqueness_score"] >= 50),
        (df["performance_score"] >= df["restaurant_avg_performance"])
        & (df["demand_match_score"] >= 42),
    ]
    choices = [
        "REMOVE",
        "REMOVE",
        "PROMOTE",
        "PROMOTE",
        "REPOSITION",
        "REPOSITION",
        "REFRESH_RECIPE",
        "REFRESH_RECIPE",
        "KEEP",
        "KEEP",
    ]
    return pd.Series(np.select(conditions, choices, default="REFRESH_RECIPE"), index=df.index)


def _strength_columns(df):
    return pd.DataFrame({
        "KEEP": (
            _score_series(df["performance_score"], 50, 65) * 45
            + _score_series(df["demand_match_score"], 42, 65) * 25
            + _score_series(df["uniqueness_score"], 45, 85) * 30
        ),
        "PROMOTE": (
            _score_series(df["performance_score"], 52, 68) * 30
            + _score_series(df["demand_match_score"], 48, 70) * 30
            + _score_series(df["trend_score"], 45, 75) * 25
            + _score_series(df["uniqueness_score"], 55, 90) * 15
        ),
        "REMOVE": (
            _score_series(45 - df["performance_score"], 0, 15) * 40
            + _score_series(df["competition_score"], 50, 85) * 35
            + _score_series(50 - df["uniqueness_score"], 0, 30) * 25
        ),
        "REFRESH_RECIPE": (
            _score_series(df["demand_match_score"], 45, 65) * 35
            + _score_series(55 - df["performance_score"], 0, 15) * 35
            + _score_series(df["competition_score"], 40, 75) * 30
        ),
        "REPOSITION": (
            _score_series(df["trend_score"], 45, 70) * 40
            + _score_series(df["demand_match_score"], 45, 65) * 30
            + _score_series(60 - df["performance_score"], 0, 15) * 30
        ),
    }, index=df.index)


def _price_optimization_scores(df):
    percentile = df["category_price_percentile"]
    performance_gap = df["performance_score"] - df["category_avg_performance"]
    price_gap = (df["price"] - df["category_median_price"]).abs()
    relative_price_gap = price_gap / df["category_median_price"].replace(0, np.nan)

    mask = (
        ((percentile >= 0.9) & (performance_gap < 0))
        | ((percentile <= 0.1) & (performance_gap >= 4))
        | (relative_price_gap >= 0.45)
    )
    scores = (
        _score_series((percentile - 0.5).abs(), 0.35, 0.5) * 45
        + _score_series(performance_gap.abs(), 2, 12) * 35
        + _score_series(price_gap, 2, 15) * 20
    )
    return scores.where(mask, 0)


def _seasonal_special_scores(df):
    seasonal_profile = (
        df["spicy"]
        + df["healthy"]
        + df["premium"]
        + df["fusion"]
        + df["trendy"]
        + df["family_friendly"]
        + df["late_night"]
    )
    mask = (
        (df["trend_score"] >= 47)
        & (df["performance_score"] >= 50)
        & (seasonal_profile > 0)
    )
    scores = (
        _score_series(df["trend_score"], 45, 75) * 45
        + _score_series(df["demand_match_score"], 45, 70) * 30
        + seasonal_profile.clip(upper=3) * 8
    )
    return scores.where(mask, 0)


def _recommendation_frame(df, recommendation_type, strength):
    output_columns = [
        "restaurant_id",
        "restaurant_name",
        "zip_or_postal_code",
        "menu_item",
        "category",
        "food_style",
        "performance_score",
        "demand_match_score",
        "trend_score",
        "competition_score",
        "uniqueness_score",
        "price",
        "price_tier",
        "flavor_profile",
        "food_trends",
        "target_audience_appeal",
        "category_price_percentile",
        "category_avg_performance",
        "category_median_price",
        "market_gap_signal",
    ]
    existing_columns = [column for column in output_columns if column in df.columns]
    recs = df[existing_columns].copy()
    recs["recommendation_type"] = recommendation_type
    recs["recommendation_strength"] = strength.round(1)
    return recs


def _item_recommendations(df):
    core_types = _core_recommendation_series(df)
    strengths = _strength_columns(df)
    column_positions = strengths.columns.get_indexer(core_types)
    core_strength = strengths.to_numpy()[np.arange(len(strengths)), column_positions]
    core_recs = _recommendation_frame(
        df,
        core_types,
        core_strength,
    )

    price_scores = _price_optimization_scores(df)
    price_recs = _recommendation_frame(
        df.loc[price_scores >= 45],
        "PRICE_OPTIMIZATION",
        price_scores.loc[price_scores >= 45],
    )

    seasonal_scores = _seasonal_special_scores(df)
    seasonal_recs = _recommendation_frame(
        df.loc[seasonal_scores >= 35],
        "SEASONAL_SPECIAL",
        seasonal_scores.loc[seasonal_scores >= 35],
    )

    return pd.concat([core_recs, price_recs, seasonal_recs], ignore_index=True)


def _build_item_row(row, recommendation_type, strength=None):
    strength = _recommendation_strength(row, recommendation_type) if strength is None else strength
    output = {
        "restaurant_id": row["restaurant_id"],
        "restaurant_name": row.get("restaurant_name", ""),
        "zip_or_postal_code": row.get("zip_or_postal_code", ""),
        "menu_item": row["menu_item"],
        "category": row.get("category", ""),
        "food_style": row.get("food_style", ""),
        "recommendation_type": recommendation_type,
        "recommendation_strength": round(float(strength), 1),
        "performance_score": round(float(row["performance_score"]), 1),
        "demand_match_score": round(float(row["demand_match_score"]), 1),
        "trend_score": round(float(row["trend_score"]), 1),
        "competition_score": round(float(row["competition_score"]), 1),
        "uniqueness_score": round(float(row["uniqueness_score"]), 1),
        "price": round(float(row["price"]), 2),
        "price_tier": row.get("price_tier", ""),
    }
    return output


def _category_market_stats(df):
    return (
        df.groupby("category")
        .agg(
            category_market_demand=("demand_match_score", "mean"),
            category_market_trend=("trend_score", "mean"),
            category_market_performance=("performance_score", "mean"),
            category_market_competition=("competition_score", "mean"),
            category_market_uniqueness=("uniqueness_score", "mean"),
            category_restaurant_count=("restaurant_id", "nunique"),
            category_item_count=("menu_item", "count"),
        )
        .reset_index()
    )


def _restaurant_category_stats(df):
    return (
        df.groupby(["restaurant_id", "restaurant_name", "category"])
        .agg(
            restaurant_category_items=("menu_item", "count"),
            restaurant_category_performance=("performance_score", "mean"),
            restaurant_category_demand=("demand_match_score", "mean"),
            best_category_item=("menu_item", _first_non_empty),
        )
        .reset_index()
    )


def _opportunity_rows(df):
    category_market = _category_market_stats(df)
    restaurant_categories = _restaurant_category_stats(df)
    restaurants = df[["restaurant_id", "restaurant_name", "zip_or_postal_code"]].drop_duplicates("restaurant_id")

    category_pool = category_market[
        (category_market["category_market_demand"] >= 47)
        & (category_market["category_market_performance"] >= 52)
        & (category_market["category"].isin(OPPORTUNITY_CATEGORIES))
    ].copy()

    category_pool["opportunity_score"] = (
        category_pool["category_market_demand"] * 0.35
        + category_pool["category_market_trend"] * 0.25
        + category_pool["category_market_performance"] * 0.25
        + category_pool["category_market_uniqueness"] * 0.15
    )

    missing = restaurants.merge(category_pool, how="cross")
    existing_categories = restaurant_categories[["restaurant_id", "category"]].drop_duplicates()
    missing = missing.merge(
        existing_categories.assign(has_category=True),
        on=["restaurant_id", "category"],
        how="left",
    )
    missing = (
        missing[missing["has_category"].isna()]
        .sort_values(["restaurant_id", "opportunity_score"], ascending=[True, False])
        .groupby("restaurant_id", as_index=False)
        .head(3)
    )

    add_rows = [
        _build_opportunity_row(row, row, "ADD_NEW_ITEM")
        for _, row in missing.iterrows()
    ]

    expandable = restaurant_categories.merge(category_market, on="category", how="left")
    expandable = expandable[
        (expandable["restaurant_category_items"] >= 2)
        & (expandable["restaurant_category_performance"] >= 54)
        & (expandable["category_market_demand"] >= 45)
        & (expandable["category"].isin(OPPORTUNITY_CATEGORIES))
    ].copy()
    expandable["opportunity_score"] = (
        expandable["restaurant_category_performance"] * 0.45
        + expandable["category_market_demand"] * 0.25
        + expandable["category_market_trend"] * 0.2
        + expandable["category_market_uniqueness"] * 0.1
    )
    expandable = (
        expandable.sort_values(["restaurant_id", "opportunity_score"], ascending=[True, False])
        .groupby("restaurant_id", as_index=False)
        .head(3)
    )

    expand_rows = [
        _build_opportunity_row(row, row, "EXPAND_CATEGORY")
        for _, row in expandable.iterrows()
    ]

    return add_rows + expand_rows


def _suggested_new_item(category):
    suggestions = {
        "Beverages": "Signature seasonal drink",
        "Burgers/Sandwiches": "Signature burger or sandwich",
        "Dumplings/Buns": "Steamed bao or dumpling sampler",
        "Pizza/Flatbreads": "Limited-time specialty pizza",
        "Salads": "Healthy lunch salad",
        "Soups": "Seasonal soup special",
        "Tacos/Burritos": "Korean BBQ taco or bowl",
        "Wings/Chicken": "Signature chicken special",
        "Pasta/Noodles": "House noodle or pasta special",
        "Seafood": "Grilled seafood plate",
        "Sushi/Poke": "Poke bowl special",
    }
    return suggestions.get(category, f"New {category} item")


def _build_opportunity_row(restaurant, opportunity, recommendation_type):
    category = opportunity["category"]
    menu_item = _suggested_new_item(category) if recommendation_type == "ADD_NEW_ITEM" else f"Expand {category}"
    strength = opportunity.get("opportunity_score", opportunity.get("restaurant_category_performance", 50))
    row = {
        **opportunity.to_dict(),
        "menu_item": menu_item,
    }
    return {
        "restaurant_id": restaurant["restaurant_id"],
        "restaurant_name": restaurant.get("restaurant_name", ""),
        "zip_or_postal_code": restaurant.get("zip_or_postal_code", ""),
        "menu_item": menu_item,
        "category": category,
        "food_style": category,
        "recommendation_type": recommendation_type,
        "recommendation_strength": round(float(strength), 1),
        "performance_score": round(float(opportunity.get("category_market_performance", 0)), 1),
        "demand_match_score": round(float(opportunity.get("category_market_demand", 0)), 1),
        "trend_score": round(float(opportunity.get("category_market_trend", 0)), 1),
        "competition_score": round(float(opportunity.get("category_market_competition", 0)), 1),
        "uniqueness_score": round(float(opportunity.get("category_market_uniqueness", 0)), 1),
        "price": 0,
        "price_tier": "opportunity",
    }


def _base_recommendation_frame(rows, recommendation_type, strength_column):
    columns = [
        "restaurant_id",
        "restaurant_name",
        "zip_or_postal_code",
        "menu_item",
        "category",
        "food_style",
        "performance_score",
        "demand_match_score",
        "trend_score",
        "competition_score",
        "uniqueness_score",
        "price",
        "price_tier",
        "flavor_profile",
        "food_trends",
        "target_audience_appeal",
        "category_price_percentile",
        "category_avg_performance",
        "category_median_price",
        "market_gap_signal",
    ]
    existing_columns = [column for column in columns if column in rows.columns]
    output = rows[existing_columns].copy()
    output["recommendation_type"] = recommendation_type
    output["recommendation_strength"] = rows[strength_column].round(1)
    return output


def _top_missing_items(item_df, recommendations, recommendation_type, score_column):
    existing_restaurants = set(
        recommendations.loc[
            recommendations["recommendation_type"].eq(recommendation_type),
            "restaurant_id",
        ]
    )
    missing_rows = item_df.loc[~item_df["restaurant_id"].isin(existing_restaurants)].copy()
    if missing_rows.empty:
        return pd.DataFrame()

    best_rows = (
        missing_rows.sort_values(["restaurant_id", score_column], ascending=[True, False])
        .drop_duplicates("restaurant_id")
    )
    return _base_recommendation_frame(best_rows, recommendation_type, score_column)


def _fallback_add_new_item(item_df, recommendations):
    existing_restaurants = set(
        recommendations.loc[
            recommendations["recommendation_type"].eq("ADD_NEW_ITEM"),
            "restaurant_id",
        ]
    )
    missing_restaurants = (
        item_df.loc[
            ~item_df["restaurant_id"].isin(existing_restaurants),
            ["restaurant_id", "restaurant_name", "zip_or_postal_code"],
        ]
        .drop_duplicates("restaurant_id")
    )
    if missing_restaurants.empty:
        return pd.DataFrame()

    category_scores = (
        item_df[item_df["category"].isin(OPPORTUNITY_CATEGORIES)]
        .groupby("category", as_index=False)
        .agg(
            performance_score=("performance_score", "mean"),
            demand_match_score=("demand_match_score", "mean"),
            trend_score=("trend_score", "mean"),
            competition_score=("competition_score", "mean"),
            uniqueness_score=("uniqueness_score", "mean"),
        )
    )
    category_scores["fallback_score"] = (
        category_scores["demand_match_score"] * 0.35
        + category_scores["trend_score"] * 0.25
        + category_scores["performance_score"] * 0.25
        + category_scores["uniqueness_score"] * 0.15
    )
    best_category = category_scores.nlargest(1, "fallback_score").iloc[0]

    rows = missing_restaurants.copy()
    rows["category"] = best_category["category"]
    rows["menu_item"] = _suggested_new_item(best_category["category"])
    rows["food_style"] = rows["category"]
    rows["performance_score"] = best_category["performance_score"]
    rows["demand_match_score"] = best_category["demand_match_score"]
    rows["trend_score"] = best_category["trend_score"]
    rows["competition_score"] = best_category["competition_score"]
    rows["uniqueness_score"] = best_category["uniqueness_score"]
    rows["price"] = 0
    rows["price_tier"] = "opportunity"
    rows["flavor_profile"] = "No data"
    rows["food_trends"] = "No data"
    rows["target_audience_appeal"] = "No data"
    rows["category_price_percentile"] = 0
    rows["category_avg_performance"] = best_category["performance_score"]
    rows["category_median_price"] = 0
    rows["market_gap_signal"] = "Fallback"
    rows["fallback_score"] = best_category["fallback_score"]
    return _base_recommendation_frame(rows, "ADD_NEW_ITEM", "fallback_score")


def _fallback_expand_category(item_df, recommendations):
    existing_restaurants = set(
        recommendations.loc[
            recommendations["recommendation_type"].eq("EXPAND_CATEGORY"),
            "restaurant_id",
        ]
    )
    category_rows = (
        item_df.loc[
            ~item_df["restaurant_id"].isin(existing_restaurants)
        ]
        .groupby(["restaurant_id", "restaurant_name", "zip_or_postal_code", "category"], as_index=False)
        .agg(
            performance_score=("performance_score", "mean"),
            demand_match_score=("demand_match_score", "mean"),
            trend_score=("trend_score", "mean"),
            competition_score=("competition_score", "mean"),
            uniqueness_score=("uniqueness_score", "mean"),
            price=("price", "median"),
        )
    )
    if category_rows.empty:
        return pd.DataFrame()

    category_rows["fallback_score"] = (
        category_rows["performance_score"] * 0.45
        + category_rows["demand_match_score"] * 0.25
        + category_rows["trend_score"] * 0.2
        + category_rows["uniqueness_score"] * 0.1
    )
    best_rows = (
        category_rows.sort_values(["restaurant_id", "fallback_score"], ascending=[True, False])
        .drop_duplicates("restaurant_id")
    )
    best_rows["menu_item"] = "Expand " + best_rows["category"]
    best_rows["food_style"] = best_rows["category"]
    best_rows["price_tier"] = "opportunity"
    best_rows["flavor_profile"] = "No data"
    best_rows["food_trends"] = "No data"
    best_rows["target_audience_appeal"] = "No data"
    best_rows["category_price_percentile"] = 0
    best_rows["category_avg_performance"] = best_rows["performance_score"]
    best_rows["category_median_price"] = best_rows["price"]
    best_rows["market_gap_signal"] = "Fallback"
    return _base_recommendation_frame(best_rows, "EXPAND_CATEGORY", "fallback_score")


def _add_missing_recommendation_fallbacks(item_df, recommendations):
    item_df = item_df.copy()
    item_df["keep_fallback_score"] = (
        item_df["performance_score"] * 0.5
        + item_df["demand_match_score"] * 0.25
        + item_df["uniqueness_score"] * 0.25
    )
    item_df["promote_fallback_score"] = (
        item_df["trend_score"] * 0.4
        + item_df["demand_match_score"] * 0.35
        + item_df["performance_score"] * 0.25
    )
    item_df["remove_fallback_score"] = (
        (100 - item_df["performance_score"]) * 0.45
        + item_df["competition_score"] * 0.35
        + (100 - item_df["uniqueness_score"]) * 0.2
    )
    item_df["refresh_fallback_score"] = (
        item_df["category_avg_demand"] * 0.35
        + (100 - item_df["performance_score"]) * 0.35
        + item_df["competition_score"] * 0.3
    )
    item_df["reposition_fallback_score"] = (
        item_df["trend_score"] * 0.4
        + item_df["demand_match_score"] * 0.3
        + (100 - item_df["performance_score"]) * 0.3
    )
    seasonal_profile = (
        item_df["spicy"]
        + item_df["healthy"]
        + item_df["premium"]
        + item_df["fusion"]
        + item_df["trendy"]
        + item_df["family_friendly"]
        + item_df["late_night"]
    )
    item_df["seasonal_fallback_score"] = (
        item_df["trend_score"] * 0.45
        + item_df["demand_match_score"] * 0.35
        + seasonal_profile * 5
    )
    item_df["price_fallback_score"] = (
        (item_df["category_price_percentile"] - 0.5).abs() * 100
        + (item_df["price"] - item_df["category_median_price"]).abs()
    )

    fallback_specs = {
        "KEEP": "keep_fallback_score",
        "PROMOTE": "promote_fallback_score",
        "REMOVE": "remove_fallback_score",
        "REFRESH_RECIPE": "refresh_fallback_score",
        "REPOSITION": "reposition_fallback_score",
        "SEASONAL_SPECIAL": "seasonal_fallback_score",
        "PRICE_OPTIMIZATION": "price_fallback_score",
    }
    fallback_frames = [
        _top_missing_items(item_df, recommendations, recommendation_type, score_column)
        for recommendation_type, score_column in fallback_specs.items()
    ]
    fallback_frames.extend([
        _fallback_add_new_item(item_df, recommendations),
        _fallback_expand_category(item_df, recommendations),
    ])
    fallback_frames = [frame for frame in fallback_frames if not frame.empty]
    if not fallback_frames:
        return recommendations
    return pd.concat([recommendations] + fallback_frames, ignore_index=True)


def apply_recommendation_rules(item_df):
    item_recommendations = _item_recommendations(item_df)
    opportunity_rows = _opportunity_rows(item_df)
    recommendations = pd.concat(
        [item_recommendations, pd.DataFrame(opportunity_rows)],
        ignore_index=True,
    )
    recommendations = _add_missing_recommendation_fallbacks(item_df, recommendations)
    recommendations = recommendations.sort_values(
        ["restaurant_id", "recommendation_type", "recommendation_strength"],
        ascending=[True, True, False],
    )
    return recommendations


def save_recommendations(recommendations, output_file=OUTPUT_FILE):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output = recommendations.copy()
    numeric_columns = output.select_dtypes(include=[np.number]).columns
    text_columns = output.columns.difference(numeric_columns)
    output[numeric_columns] = output[numeric_columns].fillna(0)
    output[text_columns] = output[text_columns].fillna("No data").replace("", "No data")
    output.to_csv(output_file, index=False)
    return output_file 


def run_recommendation_engine(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    scored_items = load_scored_items(input_file)
    item_df = prepare_items(scored_items)
    recommendations = apply_recommendation_rules(item_df)
    save_recommendations(recommendations, output_file)
    print("Recommendation engine complete.")
    print(f"Item/opportunity recommendation file: {output_file}")
    return recommendations


if __name__ == "__main__":
    run_recommendation_engine()
