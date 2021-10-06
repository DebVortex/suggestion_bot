import os
import sys
import logging


class BotLogger:

    def __init__(*args, **kwargs):
        self._logger = logging.getLogger('SuggestionBot')

        log_level = os.getenv('LOG_LEVEL', 'DEBUG')
        log_file = os.getenv('LOG_FILE')

        self._logger.setLevel(logging._nameToLevel[log_level])

        if log_file:
            self._log_handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
        else:
            self._log_handler = logging.StreamHandler(sys.stdout)

        self._handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self._logger.addHandler(self._handler)

    def debug(msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)
