import asyncio

import aiohttp
import backoff
from utils.logging_config import logger


class BaseExchangeRestAPI:
    """Base class for exchange REST APIs."""

    def __init__(
        self,
        url: str,
        product_id: str,
        last_n_days: int,
        api_key: str | None = None,
    ) -> None:
        """Initialize the REST API.

        Args:
        ----
        url: The API URL to connect to.
        product_id: The product ID to subscribe to.
        last_n_days: The number of days from which we want to get trades.
        api_key: The API key to use for authentication.

        """
        self.url = url
        self.product_id = product_id
        self.api_key = api_key
        self.last_n_days = last_n_days
        self._session: aiohttp.ClientSession | None = None
        self.semaphore = asyncio.Semaphore(10)

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
        aiohttp.ClientError,
        max_tries=3,
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
                    return await response.json()

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
