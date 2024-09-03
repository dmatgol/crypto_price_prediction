import hopsworks
import pandas as pd
from settings.config import settings


def push_data_to_feature_store(
    feature_group_name: str, feature_group_version: int, data: dict
) -> None:
    """Read ohlc volume data and push it to feature store.

    More specifically, it writes the data to the feature group specified by
    `feature_group_name` and `feature_group_version`.

    Args:
    ----
    feature_group_name (str): The name of the feature group to write to.
    feature_group_version (int): The version of the feature group to write to.
    data (dict): The data to write to the feature group.

    """
    project = hopsworks.login(
        project=settings.hopswork.project_name,
        api_key=settings.hopswork.api_key,
    )

    fs = project.get_feature_store()
    ohlc_feature_group = fs.get_or_create_feature_group(
        name=feature_group_name,
        version=feature_group_version,
        description="OHLC data coming from Kraken/Coinbase",
        primary_key=["product_id", "timestamp"],
        event_time="timestamp",
        online_enabled=True,
    )

    data = pd.DataFrame([data])
    ohlc_feature_group.insert(data)
