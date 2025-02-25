import time

import hopsworks
import pandas as pd
from hsfs.feature_store import FeatureStore
from hsfs.feature_view import FeatureView

from tools.settings import settings


class OhlcDataReader:
    """Read OHLC data from the feature store.

    The Hopsworks credentials are read from the settings class.
    """

    def __init__(
        self,
        feature_view_name: str,
        feature_view_version: int,
        feature_group_name: str | None = None,
        feature_group_version: int | None = None,
    ):
        self.feature_view_name = feature_view_name
        self.feature_view_version = feature_view_version
        self.feature_group_name = feature_group_name
        self.feature_group_version = feature_group_version

        self._fs = self._get_feature_store()

    def _get_feature_view(self) -> FeatureView:
        """Get the feature view object that reads data from the feature store."""
        if self.feature_group_name is None:
            # We try to get the feature view without creating it.
            # If it does not exist, we will raise an error because we would
            # need the feature group info to create it.
            try:
                return self._fs.get_feature_view(
                    name=self.feature_view_name,
                    version=self.feature_view_version,
                )
            except Exception:
                raise ValueError(
                    "The feature group name and version must be provided if the "
                    "feature view does not exist."
                )

        feature_group = self._fs.get_feature_group(
            name=self.feature_group_name,
            version=self.feature_group_version,
        )

        feature_view = self._fs.get_or_create_feature_view(
            name=self.feature_view_name,
            version=self.feature_view_version,
            query=feature_group.select_all(),
        )
        # if it already existed, check that its feature group name and version match
        # the ones in `self.feature_group_name` and `self.feature_group_version`
        # otherwise we raise an error
        possibly_different_feature_group = (
            feature_view.get_parent_feature_groups().accessible[0]
        )

        if (
            possibly_different_feature_group.name != feature_group.name
            or possibly_different_feature_group.version != feature_group.version
        ):
            raise ValueError(
                "The feature view and feature group names and versions do not match."
            )

        return feature_view

    def read_from_offline_store(
        self,
        product_id: list[str],
        last_n_days: int,
    ) -> pd.DataFrame:
        """Read OHLC data from the offline feature store.

        Args:
        ----
        product_id: The list of product_id(s) to read data for.
        last_n_days: The number of days to read data for.

        """
        to_timestamp_ms = int(time.time() * 1000)
        from_timestamp_ms = to_timestamp_ms - last_n_days * 24 * 60 * 60 * 1000

        feature_view = self._get_feature_view()
        features = feature_view.get_batch_data()

        # filter the features for the given product_id and time range
        features = features[features["product_id"].isin(product_id)]
        features = features[features["end_timestamp_unix"] >= from_timestamp_ms]
        features = features[features["end_timestamp_unix"] <= to_timestamp_ms]
        # sort the features by timestamp (ascending)
        features = features.sort_values(by="end_timestamp_unix").reset_index(
            drop=True
        )
        return features

    def read_from_online_store(self, product_id: list[str]) -> pd.DataFrame:
        """Read the latest OHLC data for a given product_id from the online store.

        Note: This assumes that an online feature group and its feature view are already created.
        """
        online_feature_view = self._get_feature_view()
        result = online_feature_view.get_feature_vectors(
            {"product_id": product_id}
        )
        return result

    @staticmethod
    def _get_feature_store() -> FeatureStore:
        """Get feature store object to read OHLC data."""
        project = hopsworks.login(
            project=settings.hopswork.project_name,
            api_key_value=settings.hopswork.api_key,
        )

        return project.get_feature_store()
