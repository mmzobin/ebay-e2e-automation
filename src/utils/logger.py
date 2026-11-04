import logging


def get_logger(name: str) -> logging.Logger:
    """Project logger. Output format/level is configured in pytest.ini (log_cli)."""
    return logging.getLogger(f"ebay.{name}")
