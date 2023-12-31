from blueiris_alerts.server.blueiris import blueiris_api
from blueiris_alerts.utils.exceptions import BlueIrisAlertsException


def convert_pause_duration(duration: str):
    if "30m" in duration:
        pause_duration = ["3"]
    elif "1h" in duration:
        pause_duration = ["4"]
    elif "6h" in duration:
        pause_duration = ["7", "4"]
    else:
        raise BlueIrisAlertsException(
            f"convert_pause_duration expects: 30m, 1h or 6h. Not {duration}"
        )
    return pause_duration


def pause(action: str, camera: str, duration: str = None):
    session, session_id = blueiris_api.blueiris_json_login()

    if action == "pause":
        pause_duration = convert_pause_duration(duration)
        additional_options = []
        for d in pause_duration:
            additional_options.append(f'"camera":"{camera}","pause":{d}')
    elif action == "start":
        additional_options = [f'"camera":"{camera}","pause":0']
    for option in additional_options:
        camconfig_pause = blueiris_api.blueiris_command(
            session, session_id, "camconfig", option
        )
    blueiris_api.blueiris_json_logout(session, session_id)

    return camconfig_pause
