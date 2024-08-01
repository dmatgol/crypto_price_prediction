import argparse
import re

import yaml
from api.coinbase import CoinBaseWebsocketTradeAPI
from api.kraken_api import KrakenWebsocketTradeAPI
from settings.config import Exchange, HighVolumeCoinPairs, paths


def load_config(config_file: str) -> dict:
    """Load configuration file."""
    with open(config_file) as config_file:  # type: ignore
        return yaml.safe_load(config_file)


def get_configuration_parameters() -> dict[str, str]:
    """Get the configuration parameters."""
    config = load_config(paths.config)
    args_namespace = parse_arguments()
    args_dict = vars(args_namespace)
    for key, value in args_dict.items():
        # Arg parse wont allow other arguments. No need to validate here.
        if value is not None:
            config[key] = value
    return config


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kafka_broker_address",
        type=str,
        required=False,
        help="The address of the Kafka broker.",
    )
    parser.add_argument(
        "--kafka_topic",
        type=str,
        required=False,
        help="The name of the Kafka topic.",
    )
    return parser.parse_args()


def instanteate_websocket_apis(
    config,
) -> tuple[KrakenWebsocketTradeAPI, CoinBaseWebsocketTradeAPI]:
    """Instantiate KrakenWebsocketTradeAPI and CoinBaseWebsocketTradeAPI."""
    kraken_product_ids, coinbase_product_ids = [], []
    for exchange in config["exchanges"]:
        if exchange["name"] == Exchange.Coinbase:
            coinbase_product_ids.extend(exchange["product_ids"])
            coinbase_channel = exchange["channels"]
        elif exchange["name"] == Exchange.Kraken:
            kraken_product_ids.extend(exchange["product_ids"])
            kraken_channel = exchange["channels"]
        else:
            raise ValueError("Exchange not supported.")

    kraken_apis = create_kraken_api(kraken_product_ids, kraken_channel)
    coinbase_apis = create_coinbase_api(coinbase_product_ids, coinbase_channel)
    return kraken_apis, coinbase_apis


def create_kraken_api(
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


def create_coinbase_api(
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
