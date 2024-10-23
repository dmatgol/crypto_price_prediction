from tools.ohlc_data_reader import OhlcDataReader
from tools.settings import SupportedCoins


def train(
    feature_view_name: str,
    feature_view_version: int,
    product_id: str,
    last_n_days: int,
):
    """Train a model to generate price predictions.

    The model follows the following steps:
    1. Fetch OHLC data from the feature store.
    2. Preprocess the data.
    3. Create the target variable.
    4. Train the model.

    Args:
    ----
    feature_view_name: The name of the feature view.
    feature_view_version: The version of the feature view.
    product_id: The product_id to read data for.
    last_n_days: The number of days to read data from.

    """
    ohlc_data_reader = OhlcDataReader(
        feature_view_name=feature_view_name,
        feature_view_version=feature_view_version,
    )
    ohlc_data_reader.read_from_offline_store(
        product_id=product_id,
        last_n_days=last_n_days,
    )


if __name__ == "__main__":
    train(
        feature_view_name="ohlc_feature_view",
        feature_view_version=1,
        product_id=SupportedCoins.BTC_USD.value,
        last_n_days=30,
    )
