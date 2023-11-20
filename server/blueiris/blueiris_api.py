import requests
import hashlib

from blueiris_alerts.server.settings import SETTINGS, LOGGER
from blueiris_alerts.utils.exceptions import BlueIrisError


def get_headers():
    return {"Content-Type": "application/x-www-form-urlencoded"}


def blueiris_json_login():
    LOGGER.debug("Logging into Blueiris")
    session = requests.Session()
    session.keep_alive = False

    blueiris_url = f"{SETTINGS.blueiris_web_url}/json"
    headers = get_headers()
    data = '{"cmd":"login"}'

    session_id = session.post(blueiris_url, headers=headers, data=data).json()[
        "session"
    ]

    response = hashlib.md5(
        f"{SETTINGS.blueiris_api_user}:{session_id}:{SETTINGS.blueiris_api_password}".encode(
            "utf-8"
        )
    ).hexdigest()

    login_data = f'{{"cmd":"login","session":"{session_id}","response":"{response}"}}'
    login = session.post(blueiris_url, headers=headers, data=login_data)

    if login.status_code == 200 and login.json()["result"] == "success":
        return session, login.json()["session"]
    LOGGER.error(
        f"BlueIris Login Failed: status_code: {login.status_code}, response: {login.json()}"
    )
    raise BlueIrisError("Failed to login to Blue Iris")


def blueiris_json_logout(session: requests.Session(), session_id: str):
    LOGGER.debug("Logging out of BlueIris")
    blueiris_url = f"{SETTINGS.blueiris_web_url}/json"
    headers = get_headers()
    data = f'{{"session":"{session_id}","cmd":"logout"}}'
    session.post(blueiris_url, headers=headers, data=data)


def blueiris_command(
    session: requests.Session(), session_id: str, command: str, additional_options: str
):
    LOGGER.debug(
        f"blueiris_command - session_id: {session_id}, command: {command}, additional_options: {additional_options}"
    )
    LOGGER.info(
        f"Executing Blueiris Command: {command} with additional options: {additional_options} "
    )
    blueiris_url = f"{SETTINGS.blueiris_web_url}/json"
    headers = get_headers()
    data = f'{{"session":"{session_id}","cmd":"{command}",{additional_options}}}'

    response = session.post(blueiris_url, headers=headers, data=data)

    if response.status_code == 200 and response.json()["result"] == "success":
        return response.json()

    LOGGER.error(
        f"BlueIris Command Failed: status_code: {response.status_code}, response: {response.json()}"
    )
    raise BlueIrisError("Failed to execute command")
