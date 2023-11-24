from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.logger import Logger

SETTINGS = get_settings("server")
logger = Logger(SETTINGS.log_level)

BI_LOGGER = logger.get_logger()
SLACK_LOGGER = logger.get_slack_logger()
