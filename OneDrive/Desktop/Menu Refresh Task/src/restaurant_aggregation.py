from pathlib import Path

import pandas as pd

from src.explanation_generator import format_summary_entry
from src.recommendation_engine import RECOMMENDATION_TYPES


INPUT_FILE = Path("data/processed/menu_item_recommendations.csv")
OUTPUT_FILE = Path("output/restaurant_recommendation_summary.csv")
MAX_ITEMS_PER_CELL = 5


def load_recommendations(input_file=INPUT_FILE):
    return pd.read_csv(input_file)


def _join_entries(group, limit=MAX_ITEMS_PER_CELL):
    entries = [
        format_summary_entry(row)
        for _, row in group.nlargest(limit, "recommendation_strength").iterrows()
    ]
    return " | ".join(entries)


def aggregate_restaurant_recommendations(recommendations, max_items_per_cell=MAX_ITEMS_PER_CELL):
    recommendations = recommendations.copy()
    recommendations["recommendation_strength"] = pd.to_numeric(
        recommendations["recommendation_strength"],
        errors="coerce",
    ).fillna(0)

    restaurant_base = (
        recommendations[["restaurant_id", "restaurant_name", "zip_or_postal_code"]]
        .drop_duplicates("restaurant_id")
        .sort_values("restaurant_id")
        .reset_index(drop=True)
    )

    summary = restaurant_base.copy()

    top_recommendations = (
        recommendations.sort_values(
            ["restaurant_id", "recommendation_type", "recommendation_strength"],
            ascending=[True, True, False],
        )
        .groupby(["restaurant_id", "recommendation_type"], as_index=False)
        .head(max_items_per_cell)
        .copy()
    )
    top_recommendations["entry"] = top_recommendations["menu_item"].fillna("").astype(str)
    values = (
        top_recommendations.groupby(["restaurant_id", "recommendation_type"])["entry"]
        .agg(" | ".join)
        .unstack("recommendation_type")
        .reindex(columns=RECOMMENDATION_TYPES)
        .reset_index()
    )
    summary = summary.merge(values, on="restaurant_id", how="left")

    for recommendation_type in RECOMMENDATION_TYPES:
        summary[recommendation_type] = summary[recommendation_type].fillna("No recommendation")

    summary["restaurant_name"] = (
        summary["restaurant_name"]
        .fillna("Unknown restaurant")
        .replace("", "Unknown restaurant")
    )
    summary["zip_or_postal_code"] = (
        summary["zip_or_postal_code"]
        .fillna("Unknown")
        .replace("", "Unknown")
    )

    return summary


def save_restaurant_summary(summary, output_file=OUTPUT_FILE):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        summary.to_csv(output_file, index=False)
        return output_file
    except PermissionError:
        temp_file = output_file.with_suffix(f"{output_file.suffix}.tmp")
        summary.to_csv(temp_file, index=False)
        print(
            f"Could not replace {output_file}. Close the file if it is open, "
            f"then rerun the export. Latest summary is available at {temp_file}."
        )
        return temp_file


def run_restaurant_aggregation(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    recommendations = load_recommendations(input_file)
    summary = aggregate_restaurant_recommendations(recommendations)
    saved_file = save_restaurant_summary(summary, output_file)
    print("Restaurant recommendation aggregation complete.")
    print(f"Client-facing summary file: {saved_file}")
    return summary


if __name__ == "__main__":
    run_restaurant_aggregation()
