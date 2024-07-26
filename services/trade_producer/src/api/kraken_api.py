import json

from api.base import BaseExchangeWebSocket
from utils.config import logger


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
        self._ws = self.connect(self.URL)
        self._subscribe()
        self._skip_initial_messages()

    @property
    def name(self) -> str:
        """Return the name of the exchange."""
        return "Kraken"

    # def __enter__(self):
    #     """Initialize connection upon entering async context manager."""
    #     self._ws = self.connect()
    #     self._subscribe()
    #     self._skip_initial_messages()
    #     return self

    # async def __aexit__(self, *exc_info):
    #     """Clean up connection upon exiting async context manager."""
    #     await self._ws.close()

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

    def _skip_initial_messages(self) -> None:
        """Skip first two messages of each coin pair from websocket.

        First two messages contain no trade info, just confirmation that
        subscription is sucessful.
        """
        for _ in range(len(self.product_ids)):
            self._ws.recv()
            self._ws.recv()

    def get_trades(self) -> list[dict]:
        """Read trades from the Kraken websocket and return a list of dicts.

        Returns
        -------
        list[dict]: A list of dictionaries representing the trades.

        """
        response = self._ws.recv()
        message = json.loads(response)
        if "heartbeat" in message:
            logger.info("Received heartbeat from Kraken.")
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
