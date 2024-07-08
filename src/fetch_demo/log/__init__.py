import logging
import traceback


def log_exception(exc: Exception, unhandled: bool) -> None:
    # NOTE: this function currently outputs the exception to the default
    # logger. it should be extended

    if unhandled:
        logging.error("An unhandled exception occurred:")

    for line in traceback.format_exception(exc):
        logging.error(line[:-1])
