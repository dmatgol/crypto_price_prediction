import json

from api.base import BaseExchangeWebSocket
from utils.config import logger
from websocket import WebSocket


class CoinBaseWebsocketTradeAPI(BaseExchangeWebSocket):
    """Coinbase Websocket API for trade data."""

    URL = "wss://ws-direct.exchange.coinbase.com"
    FAILOVER_URL = "wss://ws-feed.exchange.coinbase.com"

    def __init__(self, product_ids: list[str], channels: list[str]) -> None:
        """Initialize the Coinbase API with the provided websocket URL."""
        super().__init__(self.URL, product_ids, channels)
        self._ws = self.connect()
        self._subscribe()

    # async def __aenter__(self):
    #     """Initialize connection upon entering async context manager."""
    #     self._ws = await self.connect()
    #     await self._subscribe()
    #     return self

    # async def __aexit__(self, *exc_info):
    #     """Clean up connection upon exiting async context manager."""
    #     await self._ws.close()

    def connect(self) -> WebSocket | None:
        """Create a websocket connection with failover support."""
        try:
            return super().connect(self.URL)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if self.FAILOVER_URL:
                logger.info(f"Connecting to failover url: {self.FAILOVER_URL}")
                return super().connect(self.FAILOVER_URL)
            else:
                raise e

    def _create_subscribe_message(self):
        """Subscribe to the product's trade feed."""
        subscribe_message = {
            "type": "subscribe",
            "channels": [
                {"name": channel, "product_ids": self.product_ids}
                for channel in self.channels
            ],
        }
        return subscribe_message

    def get_trades(self) -> list[dict]:
        """Read trades from the Coinbase Pro WebSocket.

        Returns
        -------
        list[dict]: A list of dictionaries representing the trades.

        """
        response = self._ws.recv()
        json_response = json.loads(response)
        if "type" in json_response and json_response["type"] == "match":
            return [
                {
                    "product_id": json_response["product_id"],
                    "side": json_response["side"],
                    "price": json_response["price"],
                    "volume": json_response["size"],
                    "timestamp": json_response["time"],
                    "exchange": self.__name__,
                }
            ]
        return []
