import json
from datetime import datetime, timezone

import hopsworks
import pandas as pd
from hsfs.feature import Feature

from settings.config import settings
from utils.logging_config import logger


def push_data_to_feature_store(
    feature_group_name: str,
    feature_group_version: int,
    feature_group_primary_keys: list[str],
    feature_group_event_time: str,
    data: dict,
    online_offline: str,
) -> None:
    """Read ohlc volume data and push it to feature store.

    More specifically, it writes the data to the feature group specified by
    `feature_group_name` and `feature_group_version`.

    Args:
    ----
    feature_group_name (str): The name of the feature group to write to.
    feature_group_version (int): The version of the feature group to write to.
    feature_group_primary_keys (List[str]): The primary key of the Feature Group
    feature_group_event_time (str): The event time of the Feature Group
    data (dict): The data to write to the feature group.
    online_offline (str): Whether we are saving the `data` to the online or
        offline feature group.

    """
    project = hopsworks.login(
        project=settings.hopswork.project_name,
        api_key_value=settings.hopswork.api_key,
    )
    fs = project.get_feature_store()
    ohlc_feature_group = fs.get_or_create_feature_group(
        name=feature_group_name,
        version=feature_group_version,
        description="OHLC data coming from Kraken/Coinbase",
        primary_key=feature_group_primary_keys,
        event_time=feature_group_event_time,
        online_enabled=False,
    )

    df = pd.DataFrame(data)

    def iso_to_unix(iso_str: str) -> int:
        """Convert iso string to unix timestamp.

        Args:
        ----
        iso_str (str): Time in ISO format.

        """
        timestamp = datetime.fromisoformat(iso_str[:-1]).replace(
            tzinfo=timezone.utc
        )
        return int(timestamp.timestamp() * 1000)

    df["end_timestamp_unix"] = df["end_time"].apply(iso_to_unix)
    df["start_timestamp_unix"] = df["start_time"].apply(iso_to_unix)
    df = df.assign(
        start_time=pd.to_datetime(df["start_time"], utc=True),
        end_time=pd.to_datetime(df["end_time"], utc=True),
    )
    if online_offline == "offline":
        ohlc_feature_group.insert(
            df,
            write_options={
                "start_offline_materialization": (
                    True if online_offline == "offline" else False
                )
            },
        )
    else:
        df["start_time"] = df["start_time"].apply(lambda x: x.isoformat())
        df["end_time"] = df["end_time"].apply(lambda x: x.isoformat())

        product_id = df["product_id"].values[0]

        online_fg = fs.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key=feature_group_primary_keys,  # ONLY product_id
            description="Stores up to 14 bars per product in an array",
            online_enabled=True,
            features=[
                Feature(name="product_id", type="string"),
                Feature(
                    name="bars_array",
                    type="string",
                    online_type="varchar(1000)",
                ),
            ],
        )
        try:
            feature_view = fs.get_or_create_feature_view(
                name="online_feature_view",
                version=1,
                query=online_fg.select_all(),
            )
            result = feature_view.get_feature_vector({"product_id": product_id})
            bars_array_str = result[1]  # might be JSON
            bars_list = json.loads(bars_array_str) if bars_array_str else []
        except Exception:
            logger.error("Feature group doesn't exist or ...")
            logger.error("Key is not present in the online feature store.")
            bars_list = []

        # Append new bar
        new_bar_data = df.iloc[0].to_dict()
        if new_bar_data not in bars_list:
            bars_list.append(new_bar_data)

            # If > 14, remove the oldest
            if len(bars_list) > 14:
                bars_list.pop(0)

            # Write back
            updated_row = {
                "product_id": product_id,
                "bars_array": json.dumps(bars_list),
            }
            online_fg.insert(
                pd.DataFrame([updated_row]),
                write_options={"start_offline_backfill": False},
            )


def deserialize_timestamps(timestamps_str: str):
    """Deserialize timestamps string.

    Args:
    ----
    timestamps_str (str): The timestamps string to deserialize.

    """
    return json.loads(timestamps_str)


def serialize_timestamps(timestamps_list: list[str]):
    """Serialize timestamps string.

    Args:
    ----
    timestamps_list (list[str]): The timestamps string to deserialize.

    """
    return json.dumps(timestamps_list)
