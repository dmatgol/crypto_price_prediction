from datetime import datetime, timezone

from api.base_rest import BaseExchangeRestAPI
from utils.logging_config import logger


class KrakenRestAPI(BaseExchangeRestAPI):
    """Kraken REST API for trade data."""

    URL = "https://api.kraken.com/0/public/Trades"

    def __init__(self, product_id: str, last_n_days: int) -> None:
        """Initialize the KrakenRestAPI with the provided REST URL.

        Args:
        ----
        product_id: The product ID to fetch trades for.
        last_n_days: The number of days from which we want to get trades.

        """
        super().__init__(self.URL, product_id, last_n_days)
        self.from_ms, self.to_ms = self._init_from_to_ms(last_n_days)

        logger.info(
            f"Initializing KrakenRestAPI for product_id={self.product_id}, "
            f"from_ms={ts_to_date(self.from_ms)}, "
            f"to_ms={ts_to_date(self.to_ms)}"
        )

        # the timestamp from which we want to fetch historical data
        # this will be updated after each batch of trades fetched from the API
        self.last_trade_ms = self.from_ms

    @property
    def name(self) -> str:
        """Return the name of the exchange."""
        return "Kraken"

    def is_done(self) -> bool:
        """Check if all trades have been fetched."""
        return self.last_trade_ms >= self.to_ms

    @staticmethod
    def _init_from_to_ms(last_n_days: int) -> tuple[int, int]:
        """Return the from_ms and to_ms timestamps for the historical data.

        These values are computed using today's date at midnight and the
        last_n_days.

        Args:
        ----
        last_n_days (int): The number of days from which we want to get
        historical data.

        """
        # get the current date at midnight using UTC
        from datetime import datetime, timezone

        today_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # today_date to milliseconds
        to_ms = int(today_date.timestamp() * 1000)

        # from_ms is last_n_days ago from today, so
        from_ms = to_ms - last_n_days * 24 * 60 * 60 * 1000

        return from_ms, to_ms

    async def get_historical_trades(
        self,
    ) -> list[dict]:
        """Read historical trades from the Kraken REST API."""
        since_ns = self.last_trade_ms * 1_000_000

        params = {
            "pair": self.product_id,
            "since": since_ns,
        }

        trades = await self.get(params)
        trades = [
            {
                "product_id": self.product_id,
                "side": trade[3],
                "price": trade[0],
                "volume": trade[1],
                "timestamp": int(trade[2] * 1000),
                "exchange": self.name,
            }
            for trade in trades["result"][self.product_id]
        ]

        logger.info(
            f"Fetched {len(trades)} trades for {self.product_id}, "
            f"since={ns_to_date(since_ns)} from the Kraken REST API"
        )

        if trades[-1]["timestamp"] == self.last_trade_ms:
            self.last_trade_ms = trades[-1]["timestamp"] + 1
        else:
            self.last_trade_ms = trades[-1]["timestamp"]

        return trades


def ts_to_date(ts: int) -> str:
    """Transform a timestamp in Unix milliseconds to a human-readable date.

    Args:
    ----
    ts (int): A timestamp in Unix milliseconds

    """
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def ns_to_date(ns: int) -> str:
    """Transform a timestamp in Unix nanoseconds to a human-readable date.

    Args:
    ----
    ns (int): A timestamp in Unix nanoseconds

    """
    return datetime.fromtimestamp(ns / 1_000_000_000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )