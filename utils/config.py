import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional, overload

from blueiris_alerts.utils.exceptions import BlueIrisAlertsException


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=pathlib.Path(__file__).parent.resolve().parent / "server" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    encryption_password: str

    blueiris_web_url: str
    blueiris_api_user: str
    blueiris_api_password: str

    slack_api_token: str
    slack_signing_secret: Optional[str] = None

    log_level: Optional[str] = "INFO"


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=pathlib.Path(__file__).parent.resolve().parent / "client" / ".env",
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


@overload
def get_settings(setting: Literal["server"]) -> ServerSettings: ...


@overload
def get_settings(setting: Literal["client"]) -> ClientSettings: ...


def get_settings(setting: str) -> ServerSettings | ClientSettings:
    if setting == "server":
        settings = ServerSettings()  # type: ignore[call-arg]
    elif setting == "client":
        settings = ClientSettings()  # type: ignore[call-arg]
    else:
        raise BlueIrisAlertsException("get_settings only accepts `server` or `client`")

    return settings
