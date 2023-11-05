import requests
import hashlib

from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.exceptions import BlueIrisError

SETTINGS = get_settings("server")


def get_headers():
    return {"Content-Type": "application/x-www-form-urlencoded"}


def blueiris_json_login():
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
    raise BlueIrisError("Failed to login to Blue Iris")


def blueiris_json_logout(session: requests.Session(), session_id: str):
    blueiris_url = f"{SETTINGS.blueiris_web_url}/json"
    headers = get_headers()
    data = f'{{"session":"{session_id}","cmd":"logout"}}'
    session.post(blueiris_url, headers=headers, data=data)


def blueiris_command(
    session: requests.Session(), session_id: str, command: str, additional_options: str
):
    blueiris_url = f"{SETTINGS.blueiris_web_url}/json"
    headers = get_headers()
    data = f'{{"session":"{session_id}","cmd":"{command}",{additional_options}}}'

    response = session.post(blueiris_url, headers=headers, data=data)

    if response.status_code == 200 and response.json()["result"] == "success":
        return response.json()

    raise BlueIrisError("Failed to execute command")
