import logging

from blueiris_alerts.utils.logger import StreamToLogger


def test_stream_to_logger_write(caplog):
    logger = logging.getLogger("test_stream_write")
    stream = StreamToLogger(logger, logging.INFO)
    with caplog.at_level(logging.INFO, logger="test_stream_write"):
        stream.write("line1\nline2\n")
    assert "line1" in caplog.text
    assert "line2" in caplog.text


def test_stream_to_logger_flush():
    logger = logging.getLogger("test_stream_flush")
    stream = StreamToLogger(logger, logging.INFO)
    stream.flush()  # no-op; must not raise
