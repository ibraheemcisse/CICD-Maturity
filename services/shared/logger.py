"""
Shared logging configuration.
"""
import logging
import sys
from .config import Config


def setup_logger(service_name: str) -> logging.Logger:
    """
    Configure structured logging for a service.
    
    Args:
        service_name: Name of the service for log context
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(Config.LOG_LEVEL)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(Config.LOG_LEVEL)
    
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "service": "' + service_name + '", '
        '"level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
