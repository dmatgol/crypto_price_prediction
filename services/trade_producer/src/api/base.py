import json
from typing import Any

from utils.config import logger
from websocket import WebSocket, create_connection


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
        self._ws: WebSocket | None = None

    @staticmethod
    async def connect(url: str) -> WebSocket | None:
        """Create a websocket connection."""
        try:
            headers = {"Sec-WebSocket-Extensions": "permessage-deflate"}
            ws = await create_connection(url, header=headers)
            logger.info(f"Connection established to {url}.")
            return ws
        except Exception as e:
            logger.error(f"Connection error: {e}")
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

    async def get_trades(self) -> list[dict]:
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
                return await self.get_trades()
            except Exception as e:
                logger.error(f"Error while receiving trades: {e}")
