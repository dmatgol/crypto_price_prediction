import asyncio
import hashlib
from pathlib import Path

import aiohttp
import backoff
import pandas as pd
from api.trade import Trade
from utils.logging_config import logger


class BaseExchangeRestAPI:
    """Base class for exchange REST APIs."""

    def __init__(
        self,
        url: str,
        product_id: str,
        last_n_days: int,
        cache_dir: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize the REST API.

        Args:
        ----
        url: The API URL to connect to.
        product_id: The product ID to subscribe to.
        last_n_days: The number of days from which we want to get trades.
        api_key: The API key to use for authentication.
        cache_dir: The directory to store the cached trade data.

        """
        self.url = url
        self.product_id = product_id
        self.api_key = api_key
        self.last_n_days = last_n_days
        self._session: aiohttp.ClientSession | None = None
        self.semaphore = asyncio.Semaphore(10)
        self.use_cache = False
        if cache_dir:
            self.use_cache = True
            self.cache = CachedTradeData(cache_dir)

    async def __aenter__(self):
        """Initialize connection upon entering async context manager."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Clean up connection upon exiting async context manager."""
        if self.session:
            await self.session.close()

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, Exception),
        max_tries=10,
        jitter=backoff.full_jitter,
    )
    async def _make_request(
        self,
        payload: dict | None = None,
    ) -> dict:
        """Make an asynchronous HTTP request to the REST API.

        Args:
        ----
        payload: JSON data for POST requests.

        Returns:
        -------
        dict: The JSON response from the API.

        """
        headers = self._create_headers()

        logger.debug(f"Preparing request to {self.url} with params={payload}")

        async with self.semaphore:
            try:
                # Make sure the request is awaited
                async with self.session.get(
                    self.url,
                    params=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    logger.info(f"Request successful: {self.url}")
                    response_data = await response.json()

                    # Check if API returns "too many requests" in its own error
                    # field
                    if (
                        "error" in response_data
                        and "EGeneral:Too many requests"
                        in response_data["error"]
                    ):
                        logger.warning(
                            "API returned 'Too many requests'."
                            "Retrying with backoff..."
                        )
                        # Simulate an exception to trigger backoff
                        raise Exception("Too many requests")

                    return response_data

            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP error: {e}")
                raise e
            except Exception as e:
                logger.error(f"Request error: {e}")
                raise e

    def _create_headers(self) -> dict:
        """Create the headers for the API request."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get(self, params: dict | None = None) -> dict:
        """Perform a GET request to the REST API.

        Args:
        ----
        endpoint: The API endpoint to request.
        params: Query parameters for the request.

        Returns:
        -------
        dict: The JSON response from the API.

        """
        return await self._make_request(payload=params)

    async def get_historical_trades(self) -> list[dict]:
        """Read historical trades from the restapi and return a list of dicts.

        Returns
        -------
        list[dict]: List of trade data.

        """
        raise NotImplementedError

    async def run(self) -> list[dict]:
        """Run the REST API client to fetch historical trades.

        Args:
        ----
        last_n_days: The number of days to fetch historical data for.

        """
        try:
            trades = await self.get_historical_trades()
            return trades
        except Exception as e:
            logger.error(f"Error while receiving trades: {e}")
            raise e


class CachedTradeData:
    """Class for handling cached trade data."""

    def __init__(self, cache_dir: str) -> None:
        """Initialize the CachedTradeData class.

        Args:
        ----
        cache_dir: The directory to store the cached trade data.

        """
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)

    def read(self, url: str) -> tuple[list[Trade], int]:
        """Read trade data from the cache, given the URL.

        Args:
        ----
        url: The URL to read trade data from.

        """
        file_path = self._get_file_path(url)
        if file_path.exists():
            data = pd.read_parquet(file_path)
            return [
                Trade(**trade) for trade in data.to_dict(orient="records")
            ], data["last_trade_id"][0]
        return [], None

    def write(self, url: str, trades: list[Trade], last_trade_id: int) -> None:
        """Write trade data to the cache, given the URL.

        Args:
        ----
        url: The URL to write trade data to.
        trades: The trade data to write to the cache.
        last_trade_id: The last trade ID written to the cache.

        """
        if not trades:
            return
        file_path = self._get_file_path(url)
        data = pd.DataFrame([trade.model_dump() for trade in trades])
        data["last_trade_id"] = last_trade_id
        data.to_parquet(file_path, index=False)

    def has(self, url: str) -> bool:
        """Return True if the cache has the trade data given the url.

        Args:
        ----
        url: The URL to check if the cache has trade data for.

        """
        file_path = self._get_file_path(url)
        return file_path.exists()

    def _get_file_path(self, url: str) -> Path:
        """Get the file path for the given URL.

        Specifically, return the file where the trade data for the given
        url is (or will be) stored.

        Args:
        ----
        url: The URL to get the file path for.

        """
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{url_hash}.parquet"
