import json
from datetime import datetime, timezone

import hopsworks
import pandas as pd
from settings.config import settings


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
        online_enabled=True,
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

    ohlc_feature_group.insert(
        df,
        write_options={
            "start_offline_materialization": (
                True if online_offline == "offline" else False
            )
        },
    )

    if online_offline == "online":
        index_fg = fs.get_or_create_feature_group(
            name=f"{feature_group_name}_timestamp_index",
            version=feature_group_version,
            description="Index feature containing trade timestamps",
            primary_key=["product_id"],
            online_enabled=True,
        )
        product_id = df["product_id"]
        timestamp_unix = df["timestamp_unix"]
        index_df = index_fg.read_online(keys=[product_id])
        if index_df.empty:
            timestamps_list = []
        else:
            index_row = index_df.iloc[0]
            timestamps_str = index_row["timestamps_unix"]
            timestamps_list = deserialize_timestamps(timestamps_str)

        # Add the new timestamp to the list
        timestamps_list.append(timestamp_unix)

        # Remove timestamps older than desired time window (e.g., last 3 hours)
        current_time_unix = int(datetime.now(timezone.utc).timestamp())
        time_window_seconds = 3 * 60 * 60  # 3 hours
        cutoff_time = current_time_unix - time_window_seconds
        timestamps_list = [ts for ts in timestamps_list if ts >= cutoff_time]

        # Serialize and update the index feature group
        updated_index_data = {
            "product_id": product_id,
            "timestamps_unix": serialize_timestamps(timestamps_list),
        }
        index_df = pd.DataFrame([updated_index_data])
        index_fg.insert(index_df, write_options={"wait_for_job": False})


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
