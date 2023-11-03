class BlueIrisAlertsException(Exception):
    pass

class BlueIrisError(BlueIrisAlertsException):
    pass

class ConfigError(BlueIrisAlertsException):
    pass