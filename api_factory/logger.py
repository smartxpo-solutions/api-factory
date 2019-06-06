import logging

from pythonjsonlogger import jsonlogger


log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('(name) (levelname) (pathname) (lineno) (message) (asctime) (module)')
log_handler.setFormatter(formatter)
