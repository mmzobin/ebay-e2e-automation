import logging


def get_logger(name: str) -> logging.Logger:
    # format and level are in pytest.ini
    return logging.getLogger(f"ebay.{name}")
