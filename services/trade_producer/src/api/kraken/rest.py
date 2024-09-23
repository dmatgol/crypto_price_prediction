from datetime import datetime, timezone

from api.base_rest import BaseExchangeRestAPI
from api.trade import Trade
from utils.logging_config import logger


class KrakenRestAPI(BaseExchangeRestAPI):
    """Kraken REST API for trade data."""

    URL = "https://api.kraken.com/0/public/Trades"

    def __init__(
        self, product_id: str, last_n_days: int, cache_dir: str | None = None
    ) -> None:
        """Initialize the KrakenRestAPI with the provided REST URL.

        Args:
        ----
        product_id: The product ID to fetch trades for.
        last_n_days: The number of days from which we want to get trades.
        cache_dir: The directory to store the cached trade data.

        """
        super().__init__(self.URL, product_id, last_n_days, cache_dir)
        self.from_ms, self.to_ms = self._init_from_to_ms(last_n_days)

        logger.info(
            f"Initializing KrakenRestAPI for product_id={self.product_id}, "
            f"from_ms={ts_to_date(self.from_ms)}, "
            f"to_ms={ts_to_date(self.to_ms)}"
        )

        # Initialize trade ID with 'since' parameter (start from desired time)
        # This will be updated after each batch of trades fetched from the API
        self.last_trade_id = self.from_ms * 1_000_000
        self.last_trade_ms = self.from_ms
        self.last_trade_data = None

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
    ) -> list[Trade]:
        """Read historical trades from the Kraken REST API."""
        since_id = self.last_trade_id

        params = {"pair": self.product_id, "since": since_id}

        url = self.URL + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        if self.use_cache and self.cache.has(url):
            trades, last_trade_id = self.cache.read(url)
            logger.info(
                f"Loaded {len(trades)} for {self.product_id} from cache"
                f" since={trades[0].timestamp} to={trades[-1].timestamp}"
            )
            self.last_trade_id = last_trade_id
            self.last_trade_data = trades[-1]
        else:
            trades = await self.get(params)
            self.last_trade_id = trades["result"]["last"]
            trades = [
                Trade(
                    product_id=self.product_id,
                    side="buy" if trade[3] == "b" else "sell",
                    price=float(trade[0]),
                    volume=float(trade[1]),
                    timestamp=ts_to_date(int(trade[2] * 1000)),
                    exchange=self.name,
                )
                for trade in trades["result"][self.product_id]
            ]

            if trades:
                # Update the last trade timestamp
                self.last_trade_ms = date_to_ts(trades[-1].timestamp)
                if self.last_trade_data == trades[0]:
                    trades = trades[1:]
                self.last_trade_data = trades[-1]

            if self.use_cache:
                self.cache.write(url, trades, self.last_trade_id)
                logger.info(
                    f"Wrote {len(trades)} for {self.product_id} to cache"
                    f" since={trades[0].timestamp} to={trades[-1].timestamp}"
                )

            logger.info(
                f"Fetched {len(trades)} trades for {self.product_id}, "
                f"since={trades[0].timestamp} "
                f"to={trades[-1].timestamp} from the Kraken REST API"
            )

        return trades


def ts_to_date(ts: int) -> str:
    """Transform a timestamp in Unix milliseconds to a human-readable date.

    Args:
    ----
    ts (int): A timestamp in Unix milliseconds

    """
    return (
        datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )
        + "Z"
    )


def date_to_ts(date: str) -> int:
    """Transform a human-readable date to Unix milliseconds.

    Args:
    ----
    date (str): A human-readable date

    """
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    unix_timestamp_seconds = dt.timestamp()
    unix_timestamp_ms = int(unix_timestamp_seconds * 1000)
    return unix_timestamp_ms
