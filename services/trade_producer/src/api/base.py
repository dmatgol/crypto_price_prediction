import asyncio
import json
from typing import Any

import websockets
from utils.config import logger


class BaseExchangeWebSocket:
    """Base class for exchange websockets APIs."""

    def __init__(
        self, url: str, product_ids: list[str], channels: list[str]
    ) -> None:
        """Initialize the Websocket connection.

        Args:
        ----
        url: Websocket API url.
        product_ids: List of product ids to subscribe to.
        channels: List of channels to subscribe to.

        """
        self.url = url
        self.product_ids = product_ids
        self.channels = channels
        self._ws: websockets.WebSocketClientProtocol | None = None

    async def __aenter__(self):
        """Initialize connection upon entering async context manager."""
        self._ws = await self.connect(self.url)
        await self._subscribe()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Clean up connection upon exiting async context manager."""
        if self._ws:
            await self._ws.close()

    async def connect(
        self, url: str
    ) -> websockets.WebSocketClientProtocol | None:
        """Create a websocket connection."""
        try:
            headers = {"Sec-WebSocket-Extensions": "permessage-deflate"}
            ws = await websockets.connect(
                url, ping_interval=None, extra_headers=headers
            )
            logger.info(f"Connection established to {url}.")
            return ws
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await asyncio.sleep(5)
            return None

    async def _subscribe(self) -> None:
        """Subscribe to the product's channel feed."""
        subscribe_message = self._create_subscribe_message()
        try:
            await self._ws.send(json.dumps(subscribe_message))
            logger.info(
                f"Subscribed to {self.channels} for {self.product_ids}."
            )
        except Exception as e:
            logger.info(f"Subscription error: {e}")

    def _create_subscribe_message(self) -> dict:
        """Create the subscribe message."""
        raise NotImplementedError

    def get_trades(self) -> list[dict]:
        """Read trades from the websocket and return a list of dicts.

        Returns
        -------
        list[dict]: List of trade data.

        """
        raise NotImplementedError

    async def run(self) -> list[dict[str, Any]]:
        """Run the WebSocket listener."""
        while True:
            try:
                trades = await self.get_trades()  # type: ignore
                return trades
            except Exception as e:
                logger.error(f"Error while receiving trades: {e}")
                await asyncio.sleep(5)
