import logging
import sys


def setup_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    """Creates and configures a logger for the application."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Global project logger
logger = setup_logger()
