from pydantic import BaseModel


class Exchange:
    """Enumeration of supported exchanges.

    This class contains constants representing the names of the supported
    exchanges.
    """

    Kraken: str = "kraken"
    Coinbase: str = "coinbase"


class HighVolumeCoinPairs:
    """Enumeration of coins with high trade volume.

    This class contains constants representing the names of the coins with
    high trade volume.
    """

    ETH: str = "ETHUSD"
    BTC: str = "BTCUSD"


class Paths(BaseModel):
    """Constants used in the program."""

    config: str = "src/configs/config.yaml"


paths = Paths()
