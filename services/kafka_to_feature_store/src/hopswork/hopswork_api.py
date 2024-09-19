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
    df = df.assign(
        start_time=pd.to_datetime(df["start_time"]),
        end_time=pd.to_datetime(df["end_time"]),
    )

    ohlc_feature_group.insert(
        df,
        write_options={
            "start_offline_materialization": (
                True if online_offline == "offline" else False
            )
        },
    )
