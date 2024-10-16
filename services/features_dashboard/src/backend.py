from datetime import datetime

import hopsworks
import pandas as pd
from settings.config import settings


def get_features_from_the_store(
    feature_group_name: str,
    feature_group_version: int,
    feature_view_name: str,
    feature_view_version: int,
    time_range: tuple[datetime, datetime],
    product_id: str,
    online: bool = True,
) -> pd.DataFrame:
    """Fetch the features from the store and return them as a dataframe.

    Args:
    ----
    feature_group_name (str): The name of the feature group to fetch from.
    feature_group_version (int): The version of the feature group to fetch from.
    feature_view_name (str): The name of the feature view to fetch from.
    feature_view_version (int): The version of the feature view to fetch from.
    time_range (tuple[datetime, datetime]): The time range to fetch from and to.
    product_id (str): The product id to fetch.
    online (bool): Whether to fetch from online store.

    Returns:
    -------
    pd.DataFrame: The features as a dataframe.

    """
    project = hopsworks.login(
        project=settings.hopswork.project_name,
        api_key_value=settings.hopswork.api_key,
    )

    fs = project.get_feature_store()

    feature_group = fs.get_feature_group(
        name=feature_group_name,
        version=feature_group_version,
    )

    feature_view = fs.get_or_create_feature_view(
        name=feature_view_name,
        version=feature_view_version,
        query=feature_group.select_all(),
    )
    features: pd.DataFrame = feature_view.get_batch_data()
    product_id_filter = features["product_id"] == product_id
    time_range_utc = (
        pd.to_datetime(time_range[0]).tz_localize("UTC"),  # Localize to UTC
        pd.to_datetime(time_range[1]).tz_localize("UTC"),  # Localize to UTC
    )
    time_filter = (features["start_time"] > time_range_utc[0]) & (
        features["start_time"] <= time_range_utc[1]
    )
    features = features[time_filter & product_id_filter]
    return features
