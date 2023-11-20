from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.logger import get_logger

SETTINGS = get_settings("server")
LOGGER = get_logger(SETTINGS.log_level)
