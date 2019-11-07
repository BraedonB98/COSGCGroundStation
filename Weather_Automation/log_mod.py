import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import PurePath

log_folder = PurePath("logs")

main_log = log_folder / "runtime.log"
debug_log = log_folder / "integration_testing.log"

formatter = logging.Formatter('%(asctime)s %(levelname)s:%(module)s:%(message)s')


def setup_logger(name, log_file, level=logging.INFO, filemode='a'):
    handler = TimedRotatingFileHandler(log_file, when='D', interval=14, backupCount=4, utc=True)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


DBG = 0

# set up log file
if DBG == 1:
    log = setup_logger('debug_logger', debug_log)
else:
    log = setup_logger('logger', main_log)
