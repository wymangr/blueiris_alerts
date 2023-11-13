from pydantic_settings import BaseSettings, SettingsConfigDict
import pathlib


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


def get_settings(setting: str):
    if setting == "server":
        return ServerSettings()
    elif setting == "client":
        return ClientSettings()
