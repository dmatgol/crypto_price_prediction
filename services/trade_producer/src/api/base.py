from utils.config import logger
from websocket import create_connection


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

    async def _connect(self) -> None:
        """Create a websocket connection."""
        try:
            headers = {"Sec-WebSocket-Extensions": "permessage-deflate"}
            ws = await create_connection(self.url, header=headers)
            logger.info(f"Connection established to {self.url}.")
            return ws
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return None

    def _subscribe(self) -> None:
        """Subscribe to the product's trade feed."""
        raise NotImplementedError

    def get_trades(self) -> list[dict]:
        """Read trades from the websocket and return a list of dicts.

        Returns
        -------
            list[dict]: List of trade data.
        """
        raise NotImplementedError
