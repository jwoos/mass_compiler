import logging

from error import set_error


logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('')

def debug(*args, **kwargs):
    logger.debug(*args, **kwargs)

def info(*args, **kwargs):
    logger.info(*args, **kwargs)

def warning(*args, **kwargs):
    logger.warning(*args, **kwargs)

def error(*args, **kwargs):
    set_error()
    logger.error(*args, **kwargs)
