import json

from api.base_websocket import BaseExchangeWebSocket
from monitoring.monitoring_metrics import monitoring
from utils.logging_config import logger


class KrakenWebsocketTradeAPI(BaseExchangeWebSocket):
    """Kraken Websocket API for trade data."""

    URL = "wss://ws.kraken.com/v2"

    def __init__(self, product_ids: list[str], channels: list[str]) -> None:
        """Initialize the KrakenWebsocketAPI with the provided websocket URL.

        Args:
        ----
        product_ids: The product ID to subscribe to.
        channels: The list of channels to subscribe to.

        """
        super().__init__(self.URL, product_ids, channels)

    @property
    def name(self) -> str:
        """Return the name of the exchange."""
        return "Kraken"

    async def __aenter__(self):
        """Initialize connection upon entering async context manager."""
        await self.connect(self.URL)
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
            await self._skip_initial_messages()
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise e

    def _create_subscribe_message(self):
        """Subscribe to the product's trade feed."""
        subscribe_message = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": self.product_ids,
                "snapshot": True,
            },
        }
        return subscribe_message

    async def _skip_initial_messages(self) -> None:
        """Skip first two messages of each coin pair from websocket.

        First two messages contain no trade info, just confirmation that
        subscription is sucessful.
        """
        for _ in range(len(self.product_ids)):
            await self._ws.recv()
            await self._ws.recv()

    async def get_trades(self) -> list[dict]:
        """Read trades from the Kraken websocket and return a list of dicts.

        Returns
        -------
        list[dict]: A list of dictionaries representing the trades.

        """
        response = await self._ws.recv()
        message = json.loads(response)
        if message.get("channel", []) == "heartbeat":
            logger.info("Received heartbeat from Kraken.")
            monitoring.increment_heartbeat_count(self.name)
            return []

        trades = []
        for trade in message.get("data", []):
            trades.append(
                {
                    "product_id": trade["symbol"],
                    "side": trade["side"],
                    "price": trade["price"],
                    "volume": trade["qty"],
                    "timestamp": trade["timestamp"],
                    "exchange": self.name,
                }
            )

        return trades
