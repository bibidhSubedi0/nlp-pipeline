"""
Basic shared logger so everyone's print statements don't turn into chaos.
Usage in any module:

    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("processed envelope %s", envelope["pipeline_id"])
"""

import logging


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
