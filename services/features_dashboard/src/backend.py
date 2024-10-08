import hopsworks
import pandas as pd
from settings.config import settings


def get_features_from_the_store(
    feature_group_name: str,
    feature_group_version: int,
    feature_view_name: str,
    feature_view_version: int,
) -> pd.DataFrame:
    """Fetch the features from the store and return them as a dataframe.

    Args:
    ----
    feature_group_name (str): The name of the feature group to fetch from.
    feature_group_version (int): The version of the feature group to fetch from.
    feature_view_name (str): The name of the feature view to fetch from.
    feature_view_version (int): The version of the feature view to fetch from.

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

    return features


if __name__ == "__main__":
    print(settings)
    data = get_features_from_the_store(
        feature_group_name=settings.app_settings.feature_group,
        feature_group_version=settings.app_settings.feature_group_version,
        feature_view_name=settings.app_settings.feature_view,
        feature_view_version=settings.app_settings.feature_view_version,
    )
    print(data.head())
