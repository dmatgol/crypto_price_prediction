import time


class SnowflakeUniqueIDGenerator:
    """Snowflake ID generator."""

    def __init__(self, machine_id=0):  # Default to 0 for single machine
        """Initialize the Snowflake ID generator."""
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.epoch = 1288834974657  # Twitter's Snowflake epoch (Nov 4, 2010)

    def _current_timestamp(self):
        """Get the current timestamp in milliseconds."""
        return int(time.time() * 1000)  # Current time in milliseconds

    def generate_id(self):
        """Generate a unique Snowflake ID.

        The ID is a 64-bit number which is composed of:
        - 41-bit timestamp (millisecond precision)
        - 10-bit machine_id
        - 12-bit sequence_number

        The timestamp is the number of milliseconds since the epoch
        (Nov 4, 2010).

        The machine_id is used to identify the source of the ID. It is a number
        between 0 and 1023.

        The sequence_number is a counter which is incremented for each ID
        generated. It is a number between 0 and 4095.

        The generated ID is a 64-bit number which is a combination of the
        timestamp, machine_id, and sequence_number.
        """
        timestamp = self._current_timestamp()

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 4095  # 12-bit sequence mask
            if self.sequence == 0:
                # Wait until the next millisecond to avoid collision
                while timestamp <= self.last_timestamp:
                    timestamp = self._current_timestamp()
        else:
            self.sequence = 0  # Reset sequence for a new timestamp

        self.last_timestamp = timestamp

        # Create the Snowflake ID by combining timestamp, machine_id,
        # and sequence
        snowflake_id = (
            ((timestamp - self.epoch) << 22)
            | (self.machine_id << 12)
            | self.sequence
        )
        return snowflake_id


sf_id_generator = SnowflakeUniqueIDGenerator(
    machine_id=0
)  # Set machine_id to 0 for single machine
