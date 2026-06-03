import sys
import logging
from typing import Optional

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"


class StreamToLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        # Cleanup stderr/stdout log
        pass


class Logger:
    def __init__(self, log_level: Optional[str] = "INFO"):
        level = log_level or "INFO"
        formatter = logging.Formatter(LOG_FORMAT)

        self.root_logger = logging.getLogger("blueiris_alerts")

        # Only configure handlers once — prevents duplicate lines when Logger
        # is instantiated in both the client and server within the same process.
        if not self.root_logger.handlers:
            self.root_logger.setLevel(level)

            file_handler = logging.FileHandler("blueiris_alerts.log", mode="a")
            file_handler.setFormatter(formatter)
            self.root_logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.root_logger.addHandler(console_handler)

            # Redirect stderr to the logger at ERROR so unhandled tracebacks
            # are captured.  Leave stdout alone — print() is not used for logging.
            sys.stderr = StreamToLogger(self.root_logger, logging.ERROR)
        else:
            # Already configured; just update the level in case it changed.
            self.root_logger.setLevel(level)

    def get_logger(self):
        return self.root_logger

    def get_slack_logger(self):
        slack_logger = logging.getLogger("slack")
        # Match the application log level so DEBUG requests produce SDK debug output.
        slack_logger.setLevel(self.root_logger.level)
        return slack_logger
