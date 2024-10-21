import json
from typing import Any

from api.base_websocket import BaseExchangeWebSocket
from api.trade import Trade
from monitoring.monitoring_metrics import monitoring
from utils.logging_config import logger


class CoinBaseWebsocketTradeAPI(BaseExchangeWebSocket):
    """Coinbase Websocket API for trade data."""

    URL = "wss://ws-feed.exchange.coinbase.com"
    FAILOVER_URL = "wss://ws-feed.exchange.coinbase.com"

    def __init__(self, product_ids: list[str], channels: list[str]) -> None:
        """Initialize the Coinbase API with the provided websocket URL."""
        super().__init__(self.URL, product_ids, channels)

    @property
    def name(self) -> str:
        """Return the name of the exchange."""
        return "Coinbase"

    async def __aenter__(self):
        """Initialize connection upon entering async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, *exc_info):
        """Clean up connection upon exiting async context manager."""
        if self._ws:
            await self._ws.close()

    async def connect(self, url: str | None = None):
        """Create a websocket connection with failover support."""
        url = url or self.URL
        try:
            await super().connect(url)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if self.FAILOVER_URL:
                logger.info(f"Connecting to failover url: {self.FAILOVER_URL}")
                await super().connect(self.FAILOVER_URL)
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
        logger.info(subscribe_message)
        return subscribe_message

    async def get_trades(self) -> list[dict[str, Any]]:
        """Read trades from the Coinbase Pro WebSocket.

        Returns
        -------
        list[dict]: A list of dictionaries representing the trades.

        """
        try:
            response = await self._ws.recv()
            json_response = json.loads(response)
            if "type" in json_response and json_response["type"] == "heartbeat":
                logger.info("Received heartbeat from Coinbase.")
                monitoring.increment_heartbeat_count(self.name)
                return []

            if "type" in json_response and json_response["type"] == "ticker":
                return [
                    Trade(
                        product_id=json_response["product_id"],
                        side=json_response["side"],
                        price=float(json_response["price"]),
                        volume=float(json_response["last_size"]),
                        timestamp=json_response["time"],
                        exchange=self.name,
                    )
                ]
        except Exception as e:
            logger.error(f"Error while reading trades: {e}")
        return []
