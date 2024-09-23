import re

from api.coinbase.websocket import CoinBaseWebsocketTradeAPI
from api.kraken.rest import KrakenRestAPI
from api.kraken.websocket import KrakenWebsocketTradeAPI
from settings.config import HighVolumeCoinPairs, SupportedExchanges, settings


def instanteate_apis() -> (
    tuple[KrakenWebsocketTradeAPI, CoinBaseWebsocketTradeAPI]
):
    """Instantiate KrakenWebsocketTradeAPI and CoinBaseWebsocketTradeAPI."""
    kraken_product_ids, coinbase_product_ids = [], []
    for exchange in settings.exchanges:
        if exchange.name == SupportedExchanges.COINBASE:
            coinbase_product_ids.extend(exchange.product_ids)
            coinbase_channel = exchange.channels
        elif exchange.name == SupportedExchanges.KRAKEN:
            kraken_product_ids.extend(exchange.product_ids)
            kraken_channel = exchange.channels
        else:
            raise ValueError("Exchange not supported.")

    if settings.live_or_historical_settings.live_or_historical == "live":
        kraken_apis = (
            create_kraken_websocket_api(kraken_product_ids, kraken_channel)
            if kraken_product_ids
            else []
        )
        coinbase_apis = (
            create_coinbase_websocket_api(
                coinbase_product_ids, coinbase_channel
            )
            if coinbase_product_ids
            else []
        )
    elif (
        settings.live_or_historical_settings.live_or_historical == "historical"
    ):
        kraken_apis = create_kraken_rest_api(
            kraken_product_ids,
            settings.live_or_historical_settings.last_n_days,
            settings.live_or_historical_settings.cache_dir_historical_data,
        )
        coinbase_apis = []
    return kraken_apis, coinbase_apis


def create_kraken_websocket_api(
    product_ids: list[str], channels: list[str]
) -> KrakenWebsocketTradeAPI:
    """Create a KrakenWebsocketTradeAPI instance for the given product_id.

    Create separate instance for high-volume coins. As of now, those are
    only BTC and ETH.

    Args:
    ----
    product_ids: The product ID to subscribe to.
    channels: The list of channels to subscribe to.

    """
    kraken_apis = []
    low_volume_coins = []
    for product_id in product_ids:
        if (
            re.sub(r"[\\/\-\.]", "", product_id)
            in HighVolumeCoinPairs.__dict__.values()
        ):
            kraken_apis.append(
                KrakenWebsocketTradeAPI(
                    product_ids=[product_id], channels=channels
                )
            )
        else:
            low_volume_coins.append(product_id)
    if low_volume_coins:
        kraken_apis.append(
            KrakenWebsocketTradeAPI(
                product_ids=low_volume_coins,
                channels=channels,
            )
        )
    return kraken_apis


def create_coinbase_websocket_api(
    product_ids: list[str], channels: list[str]
) -> CoinBaseWebsocketTradeAPI:
    """Create a CoinbaseWebsocketTradeAPI instance for the given product_id.

    Create separate instance for high-volume coins. As of now, those are
    only BTC and ETH.

    Args:
    ----
    product_ids: The product ID to subscribe to.
    channels: The list of channels to subscribe to.

    """
    coinbase_apis = []
    low_volume_coins = []
    for product_id in product_ids:
        if (
            re.sub(r"[\\/\-\.]", "", product_id)
            in HighVolumeCoinPairs.__dict__.values()
        ):
            coinbase_apis.append(
                CoinBaseWebsocketTradeAPI(
                    product_ids=[product_id], channels=channels
                )
            )
        else:
            low_volume_coins.append(product_id)
    if low_volume_coins:
        coinbase_apis.append(
            CoinBaseWebsocketTradeAPI(
                product_ids=low_volume_coins,
                channels=channels,
            )
        )
    return coinbase_apis


def create_kraken_rest_api(
    product_ids: list[str], last_n_days: int, cache_dir: str | None = None
) -> KrakenRestAPI:
    """Create a KrakenRestAPI instance for the given product_id.

    Args:
    ----
    product_ids: The product ID to subscribe to.
    last_n_days: The number of days from which we want to get trades.
    cache_dir: The directory to store the cached trade data.

    """
    kraken_rest_apis = []
    for product_id in product_ids:
        kraken_api_instance = KrakenRestAPI(product_id, last_n_days, cache_dir)
        kraken_rest_apis.append(kraken_api_instance)
    return kraken_rest_apis
