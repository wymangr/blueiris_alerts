import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from blueiris_alerts.utils.exceptions import BlueIrisAlertsException


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"{pathlib.Path(__file__).parent.resolve().parent}/server/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    encryption_password: str

    blueiris_web_url: str
    blueiris_api_user: str
    blueiris_api_password: str

    slack_api_token: str

    log_level: Optional[str] = "INFO"


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"{pathlib.Path(__file__).parent.resolve().parent}/client/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    encryption_password: str

    server_url: str
    slack_api_token: str
    slack_channel: str

    blueiris_web_url: str
    blueiris_api_user: str
    blueiris_api_password: str

    log_level: Optional[str] = "INFO"


def get_settings(setting: str):
    if setting == "server":
        settings = ServerSettings()
    elif setting == "client":
        settings = ClientSettings()
    else:
        raise BlueIrisAlertsException("get_settings only accepts `server` or `client`")

    return settings
