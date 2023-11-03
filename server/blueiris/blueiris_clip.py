import re
import urllib
import time

from blueiris_alerts.server.blueiris import blueiris_api
from blueiris_alerts.utils.exceptions import BlueIrisError


def get_clip(alert_clip):
    session, session_id = blueiris_api.blueiris_json_login()
    clips = blueiris_api.blueiris_command(
        session, session_id, "alertlist", '"camera":"index"'
    )
    blueiris_api.blueiris_json_logout(session, session_id)

    clip_path = None
    clip_size = None
    clip_length = 10000

    for clip in clips["data"]:
        if alert_clip == clip["file"]:
            clip_path = clip["path"]
            clip_size = clip["filesize"]
            break
    if not clip_path or not clip_size:
        raise BlueIrisError("Unable to find alert clip")
    if "sec" in clip_size:
        clip_length = int(re.findall(r"^\d*", clip_size)[0]) * 1000
    elif "m" in clip_size and "s" in clip_size:
        m = int(re.findall(r"^\d*", clip_size)[0]) * 60
        s = int(re.findall(r"m\d*", clip_size)[0].replace("m", ""))
        clip_length = (m + s) * 1000
    return gen_clip(clip_path, clip_length)


def gen_clip(clip_path, clip_length):
    clip_images = []
    for r in range(200, int(clip_length), 200):
        clip_url = f"{blueiris_api.SETTINGS.blueiris_web_url}/file/clips/{clip_path}?time={r}&user={blueiris_api.SETTINGS.blueiris_api_user}&pw={blueiris_api.SETTINGS.blueiris_api_password}&q={10}"
        contents = urllib.request.urlopen(clip_url).read()
        clip_images.append(contents)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + contents + b"\r\n")
    while True:
        for contents in clip_images:
            time.sleep(0.1)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + contents + b"\r\n")
