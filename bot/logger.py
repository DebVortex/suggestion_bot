import os
import sys
import logging


class BotLogger:

    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger('SuggestionBot')

        log_level = os.getenv('LOG_LEVEL', 'DEBUG')
        log_file = os.getenv('LOG_FILE')

        self._logger.setLevel(logging._nameToLevel[log_level])

        if log_file:
            self._log_handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
        else:
            self._log_handler = logging.StreamHandler(sys.stdout)

        self._log_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self._logger.addHandler(self._log_handler)

    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)
