"""
Shared logging configuration.
"""
import logging
import sys

from .config import Config


def setup_logger(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(Config.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(Config.LOG_LEVEL)
    handler.setFormatter(
        logging.Formatter(
            '{"time": "%(asctime)s", "service": "'
            + service_name
            + '", "level": "%(levelname)s", "message": "%(message)s"}'
        )
    )
    logger.addHandler(handler)
    return logger
