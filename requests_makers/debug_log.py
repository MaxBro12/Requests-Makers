import logging
from typing import Literal


Level = Literal['debug', 'warning', 'info', 'error', 'crit']

def create_log(
    log: Exception | str,
    level_name: Level = 'debug',
    loggers_names: list | tuple | None = None
):
    if loggers_names is None:
        loggers_names = [name for name in logging.root.manager.loggerDict]

    loggers = [logging.getLogger(logger_name) for logger_name in loggers_names]

    for logger in loggers:

        log_exc = False
        if type(log) is not str:
            log_exc = True
        match level_name:
            case 'debug':
                logger.debug(log, exc_info=log_exc)
            case 'warning':
                logger.warning(log, exc_info=log_exc)
            case 'info':
                logger.info(log, exc_info=log_exc)
            case 'error':
                logger.error(log, exc_info=log_exc)
            case 'crit':
                logger.critical(log, exc_info=log_exc)
