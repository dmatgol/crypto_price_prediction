import sys

from loguru import logger

# Remove the default logger
logger.remove()

# Add a new logger with custom configuration for stderr
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# Add a new logger with custom configuration for file
logger.add(
    "logs/file_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - "
    "{message}",
    level="INFO",
    colorize=False,
)
