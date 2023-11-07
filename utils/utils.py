from blueiris_alerts.utils.exceptions import ConfigError


def get_blueiris_auth_url(base_url: str, user: str, password: str):
    if "https://" in base_url:
        index = 8
    elif "http://" in base_url:
        index = 7
    else:
        raise ConfigError("blueiris_web_url needs to be a http or https address")

    return f"{base_url[:index]}{user}:{password}@{base_url[index:]}"
