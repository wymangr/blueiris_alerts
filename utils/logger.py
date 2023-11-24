import sys
import logging

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
    def __init__(self, log_level: str):
        logging.basicConfig(
            level=log_level,
            format=LOG_FORMAT,
            filename="blueiris_alerts.log",
            filemode="a",
        )

        formatter = logging.Formatter(LOG_FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(formatter)

        self.root_logger = logging.getLogger()
        self.root_logger.addHandler(console)
        sys.stdout = StreamToLogger(self.root_logger, logging.INFO)
        sys.stderr = StreamToLogger(self.root_logger, logging.ERROR)

    def get_logger(self):
        return self.root_logger

    def get_slack_logger(self):
        slack_logger = logging.getLogger("slack")
        slack_logger.setLevel(logging.INFO)
        return slack_logger
