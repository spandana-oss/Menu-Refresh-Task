RECOMMENDATION_ACTIONS = {
    "KEEP": "keep",
    "PROMOTE": "promote",
    "REMOVE": "remove or replace",
    "REFRESH_RECIPE": "refresh recipe",
    "REPOSITION": "reposition",
    "ADD_NEW_ITEM": "add item",
    "SEASONAL_SPECIAL": "seasonal special",
    "EXPAND_CATEGORY": "expand category",
    "PRICE_OPTIMIZATION": "review price",
}


def _score_phrase(value, high_text, low_text, high=65, low=40):
    if value >= high:
        return high_text
    if value <= low:
        return low_text
    return ""


def _compact(parts):
    return ", ".join(part for part in parts if part)


def explain_item_recommendation(row, recommendation_type):
    item = row.get("menu_item", "Item")
    category = row.get("category", "category")
    performance = row.get("performance_score", 0)
    demand = row.get("demand_match_score", 0)
    trend = row.get("trend_score", 0)
    competition = row.get("competition_score", 0)
    uniqueness = row.get("uniqueness_score", 0)
    price_percentile = row.get("category_price_percentile", 0.5)
    price_tier = row.get("price_tier", "mid")
    market_gap = row.get("market_gap_signal", "Balanced")

    if recommendation_type == "KEEP":
        parts = [
            _score_phrase(performance, "stable performer", "", high=55, low=0),
            _score_phrase(demand, "good demand", "", high=55, low=0),
            _score_phrase(uniqueness, "distinctive", "", high=65, low=0),
        ]
        return _compact(parts) or "balanced scores"

    if recommendation_type == "PROMOTE":
        parts = [
            _score_phrase(trend, "strong trend", "", high=55, low=0),
            _score_phrase(demand, "strong demand", "", high=55, low=0),
            "opportunity gap" if market_gap == "Opportunity Gap" else "",
            _score_phrase(uniqueness, "low competition", "", high=65, low=0),
        ]
        return _compact(parts) or "strong signals"

    if recommendation_type == "REMOVE":
        parts = [
            _score_phrase(performance, "", "weak performance", high=101, low=45),
            _score_phrase(competition, "oversaturated", "", high=60, low=0),
            _score_phrase(uniqueness, "", "low uniqueness", high=101, low=45),
            _score_phrase(demand, "", "low demand", high=101, low=40),
        ]
        return _compact(parts) or "weak signals"

    if recommendation_type == "REFRESH_RECIPE":
        parts = [
            _score_phrase(demand, "demand exists", "", high=50, low=0),
            _score_phrase(performance, "", "weak execution", high=101, low=52),
            _score_phrase(competition, "crowded market", "", high=50, low=0),
        ]
        return _compact(parts) or f"{category} demand, weak execution"

    if recommendation_type == "REPOSITION":
        parts = [
            _score_phrase(trend, "trend fit", "", high=50, low=0),
            _score_phrase(demand, "demand fit", "", high=50, low=0),
            _score_phrase(performance, "", "underperforming", high=101, low=55),
        ]
        return _compact(parts) or "good item, weak positioning"

    if recommendation_type == "SEASONAL_SPECIAL":
        parts = [
            _score_phrase(trend, "seasonal trend fit", "", high=50, low=0),
            row.get("food_trends", "") if row.get("food_trends", "") != "General" else "",
        ]
        return _compact(parts) or "limited-time fit"

    if recommendation_type == "PRICE_OPTIMIZATION":
        if price_percentile >= 0.9:
            return f"high vs {category} peers"
        if price_percentile <= 0.1:
            return f"low vs {category} peers"
        return f"review {price_tier} price"

    return f"{item} matched {recommendation_type.lower()} rules"


def explain_opportunity(row, recommendation_type):
    category = row.get("category", row.get("menu_item", "category"))
    demand = row.get("category_market_demand", 0)
    trend = row.get("category_market_trend", 0)
    performance = row.get("restaurant_category_performance", 0)
    uniqueness = row.get("category_market_uniqueness", 0)

    if recommendation_type == "ADD_NEW_ITEM":
        parts = [
            _score_phrase(demand, "local demand", "", high=50, low=0),
            _score_phrase(trend, "trend fit", "", high=45, low=0),
            _score_phrase(uniqueness, "less crowded", "", high=60, low=0),
            "missing category",
        ]
        return _compact(parts)

    if recommendation_type == "EXPAND_CATEGORY":
        parts = [
            _score_phrase(performance, "strong category", "", high=55, low=0),
            _score_phrase(demand, "market demand", "", high=50, low=0),
            _score_phrase(trend, "variant potential", "", high=45, low=0),
        ]
        return _compact(parts) or f"{category} has expansion signal"

    return f"{category} matched {recommendation_type.lower()} opportunity rules"


def suggested_action(recommendation_type, row):
    return RECOMMENDATION_ACTIONS.get(recommendation_type, "Review this recommendation.")


def format_summary_entry(row):
    return row.get("menu_item", row.get("category", "Recommendation"))
