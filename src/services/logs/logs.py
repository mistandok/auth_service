"""Модуль предназначен для реализации формирования логгера для других модулей."""
import logging
import sys
from functools import lru_cache

from .settings import BASE_FORMAT, BASE_LOG_LEVEL, BASE_LOGGER_NAME


@lru_cache()
def get_logger() -> logging.Logger:
    """
    Функция формирует логгер для заданного пространства имен.
    Returns:
        None
    """
    logger = logging.getLogger(BASE_LOGGER_NAME)
    logger.setLevel(BASE_LOG_LEVEL)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_formatter = logging.Formatter(BASE_FORMAT)
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)

    return logger
