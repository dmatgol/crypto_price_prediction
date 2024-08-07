from prometheus_client import Counter, Summary, start_http_server


class MonitoringMetrics:
    """Metrics class to track performance of app."""

    def __init__(self, port: int = 8000):
        """Initialize the metrics."""
        self.request_time = Summary(
            "request_processing_seconds",
            "Time spent processing request",
            ["exchange"],
        )
        self.request_count = Counter(
            "request_count", "Total number of requests", ["exchange"]
        )

        self.heartbeat_responses = Counter(
            "heartbeat_responses",
            "Total number of heartbeat responses",
            ["exchange"],
        )

        # Start the HTTP server to expose metrics
        start_http_server(port)

    def observe_request(self, exchange: str, metric: float):
        """Observe a specific metric."""
        self.request_time.labels(exchange=exchange).observe(metric)

    def increment_request_count(self, exchange: str):
        """Count the number of requests."""
        self.request_count.labels(exchange=exchange).inc()

    def increment_heartbeat_count(self, exchange: str):
        """Increment the number of heartbeat responses."""
        self.heartbeat_responses.labels(exchange=exchange).inc()


monitoring = MonitoringMetrics(port=8000)
