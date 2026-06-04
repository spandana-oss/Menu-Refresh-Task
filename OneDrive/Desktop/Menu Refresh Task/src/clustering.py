from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import math
import numpy as np
import pandas as pd


def _split_tags(value):
    if value != value:
        return []
    return [
        tag.strip().lower()
        for tag in str(value).split(',')
        if tag.strip()
    ]


def _row_tags(row):
    tags = []
    for column in ['style', 'cuisines', 'restaurant_type']:
        tags.extend(_split_tags(row.get(column)))
    return tags


def _tag_matches_keyword(tag, keyword):
    if keyword == 'bar':
        return tag in ['bar', 'bars', 'cocktail bar', 'cocktail bars']
    if keyword == 'cafe':
        return tag in ['cafe', 'cafes', 'coffee shop', 'coffee shops']
    if keyword == 'qsr':
        return tag == 'qsr'
    return keyword in tag


def _has_any(tags, keywords):
    return any(
        _tag_matches_keyword(tag, keyword)
        for tag in tags
        for keyword in keywords
    )


def _build_food_behavior(df, geo_column):
    behavior_rows = []

    category_keywords = {
        'fast_food_share': [
            'fast food',
            'qsr',
            'burger',
            'fried chicken',
            'chicken wings',
            'wings',
            'sandwich'
        ],
        'healthy_share': [
            'healthy',
            'salad',
            'vegetarian',
            'vegan',
            'juice',
            'smoothie',
            'poke',
            'mediterranean'
        ],
        'beverage_share': [
            'coffee',
            'cafe',
            'juice',
            'smoothie',
            'bar',
            'cocktail'
        ],
        'wings_share': [
            'wings',
            'chicken wings',
            'wings joint'
        ]
    }

    for geo_value, group in df.groupby(geo_column):
        all_tags = []
        category_counts = {category: 0 for category in category_keywords}

        for _, row in group.iterrows():
            tags = _row_tags(row)
            all_tags.extend(tags)

            for category, keywords in category_keywords.items():
                if _has_any(tags, keywords):
                    category_counts[category] += 1

        restaurant_count = len(group)
        unique_tags = set(all_tags)
        dominant_tag_count = max(
            (all_tags.count(tag) for tag in unique_tags),
            default=0
        )

        rating = pd.to_numeric(group.get('rating_value', 0), errors='coerce')
        reviews = pd.to_numeric(group.get('review_count', 0), errors='coerce')
        customer_engagement = (
            rating.fillna(0).clip(lower=0).mean() *
            math.log1p(reviews.fillna(0).clip(lower=0).sum())
        )

        behavior = {
            geo_column: geo_value,
            'restaurant_count': restaurant_count,
            'cuisine_variety': len(unique_tags) / max(restaurant_count, 1),
            'cuisine_focus': dominant_tag_count / max(len(all_tags), 1),
            'customer_engagement': customer_engagement
        }

        for category, count in category_counts.items():
            behavior[category] = count / max(restaurant_count, 1)

        behavior_rows.append(behavior)

    return behavior_rows


CLUSTER_PROFILE_COLUMNS = [
    'income_level',
    'young_demand_level',
    'senior_demand_level',
    'competition_level',
    'growth_level',
    'cuisine_variety_level',
    'customer_engagement_level',
    'fast_food_level',
    'healthy_level',
    'beverage_level',
    'wings_level'
]


def prepare_clustering_features(df):
    df = df.copy()

    if 'COMPETITOR_DENSITY' in df.columns:
        df['competition_score'] = pd.to_numeric(
            df['COMPETITOR_DENSITY'],
            errors='coerce'
        )
    else:
        df['competition_score'] = (
            df['ESTAB'] /
            df['POP'].replace(0, np.nan)
        )

    df['AGE_TOTAL'] = (
        df['AGE_18_24'] +
        df['AGE_25_34'] +
        df['AGE_35_44'] +
        df['AGE_55_64'] +
        df['AGE_65_PLUS']
    )

    df['AGE_TOTAL'] = df['AGE_TOTAL'].replace(0, np.nan)

    df['PCT_18_24'] = (
        df['AGE_18_24'] / df['AGE_TOTAL']
    )

    df['PCT_25_34'] = (
        df['AGE_25_34'] / df['AGE_TOTAL']
    )

    df['PCT_65_PLUS'] = (
        df['AGE_65_PLUS'] / df['AGE_TOTAL']
    )

    return df


def build_cluster_profile(df_cluster):
    return df_cluster.groupby(
        'cluster_id'
    )[CLUSTER_PROFILE_COLUMNS].mean()


def create_clusters(df, n_clusters=6):
    geo_column = 'ZCTA' if 'ZCTA' in df.columns else 'FIPS'
    df = prepare_clustering_features(df)

    # -----------------------------
    # Aggregate at ZIP level when available
    # -----------------------------
    df_cluster = df.groupby(geo_column).agg({
        'MEDIAN_INCOME': 'first',
        'PCT_18_24': 'first',
        'PCT_25_34': 'first',
        'PCT_65_PLUS': 'first',
        'competition_score': 'mean',
        'population_growth_rate': 'first'
    }).reset_index()

    df_behavior = _build_food_behavior(df, geo_column)
    df_cluster = df_cluster.merge(
        pd.DataFrame(df_behavior),
        
        on=geo_column,
        how='left'
    )

    # -----------------------------
    # FEATURE ENGINEERING
    # -----------------------------
    df_cluster['young_demand'] = (
        df_cluster['PCT_18_24'] + df_cluster['PCT_25_34']
    )
    df_cluster['senior_demand'] = df_cluster['PCT_65_PLUS']

    # Put every clustering signal on the same 0-1 rank scale so income has
    # the same model importance as demand, competition, and growth.
    ranked_features = {
        'income_level': 'MEDIAN_INCOME',
        'young_demand_level': 'young_demand',
        'senior_demand_level': 'senior_demand',
        'competition_level': 'competition_score',
        'growth_level': 'population_growth_rate',
        'cuisine_variety_level': 'cuisine_variety',
        'cuisine_focus_level': 'cuisine_focus',
        'customer_engagement_level': 'customer_engagement',
        'fast_food_level': 'fast_food_share',
        'healthy_level': 'healthy_share',
        'beverage_level': 'beverage_share',
        'wings_level': 'wings_share'
    }

    for ranked_name, source_column in ranked_features.items():
        df_cluster[ranked_name] = df_cluster[source_column].rank(
            method='average',
            pct=True
        )


    features = [
        'income_level',
        'young_demand_level',
        'senior_demand_level',
        'competition_level',
        'growth_level',
        'cuisine_variety_level',
        'cuisine_focus_level',
        'customer_engagement_level',
        'fast_food_level',
        'healthy_level',
        'beverage_level',
        'wings_level'
    ]

    X = df_cluster[features].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # -----------------------------
    # KMEANS
    # -----------------------------
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df_cluster['cluster_id'] = kmeans.fit_predict(X_scaled)

    # -----------------------------
    # MAP BACK
    # -----------------------------
    df = df.merge(
        df_cluster[[geo_column, 'cluster_id']],
        on=geo_column,
        how='left'
    )

    return df, df_cluster, build_cluster_profile(df_cluster)
