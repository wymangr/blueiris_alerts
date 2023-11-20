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


def get_logger(log_level: str) -> logging.RootLogger:
    logging.basicConfig(
        level=log_level, format=LOG_FORMAT, filename="blueiris_alerts.log", filemode="a"
    )

    console = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    logger = logging.getLogger()
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    return logger
