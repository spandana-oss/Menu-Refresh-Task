from pathlib import Path

import pandas as pd

from src.recommendation_engine import (
    OUTPUT_FILE as ITEM_RECOMMENDATION_FILE,
    run_recommendation_engine,
)
from src.restaurant_aggregation import (
    OUTPUT_FILE as RESTAURANT_SUMMARY_FILE,
    run_restaurant_aggregation,
)


JSON_OUTPUT_FILE = Path("output/restaurant_recommendation_summary.json")


def save_json_summary(summary, output_file=JSON_OUTPUT_FILE):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        summary.to_json(output_file, orient="records", indent=2)
        return output_file
    except PermissionError:
        temp_file = output_file.with_suffix(f"{output_file.suffix}.tmp")
        summary.to_json(temp_file, orient="records", indent=2)
        print(
            f"Could not replace {output_file}. Close the file if it is open, "
            f"then rerun the export. Latest JSON summary is available at {temp_file}."
        )
        return temp_file


def run_final_recommendation_exports():
    run_recommendation_engine(output_file=ITEM_RECOMMENDATION_FILE)
    summary = run_restaurant_aggregation(output_file=RESTAURANT_SUMMARY_FILE)
    json_file = save_json_summary(summary)
    print(f"JSON summary file: {json_file}")
    return summary


def load_restaurant_summary(path=RESTAURANT_SUMMARY_FILE):
    return pd.read_csv(path)


if __name__ == "__main__":
    run_final_recommendation_exports()
