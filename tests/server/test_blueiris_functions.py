import pytest

from pytest_mock import MockFixture
from blueiris_alerts.server.blueiris import (
    blueiris_api,
    blueiris_camconfig,
    blueiris_clip,
)
from blueiris_alerts.utils.exceptions import BlueIrisError, BlueIrisAlertsException

RESPONSE = {"result": "success", "session": "session"}


@pytest.fixture
def setup_session_post(mocker):
    session_post_mock = mocker.patch("requests.Session.post")
    session_post_mock.return_value.status_code = 200
    session_post_mock.return_value.json.return_value = RESPONSE
    return session_post_mock


def test_blueiris_camconfig(mocker: MockFixture):
    durations = {"30m": ["3"], "1h": ["4"], "6h": ["7", "4"]}

    blueiris_command_mock = mocker.patch(
        "blueiris_alerts.server.blueiris.blueiris_camconfig.blueiris_api"
    )
    blueiris_command_mock.blueiris_json_login.return_value = "session", "session_id"
    blueiris_command_mock.blueiris_command.return_value = RESPONSE
    blueiris_command_mock.return_value.blueiris_json_logout

    for duration in durations:
        puase_out = blueiris_camconfig.pause("pause", "camera", duration)
        assert puase_out == RESPONSE

    pause_start = blueiris_camconfig.pause("start", "camera")
    assert pause_start == RESPONSE


def test_blueiris_api(setup_session_post):
    test_session, test_session_id = blueiris_api.blueiris_json_login()
    setup_session_post.assert_called()
    assert test_session_id == "session"

    test_command = blueiris_api.blueiris_command(
        test_session, test_session_id, "command", "additional_options"
    )
    assert test_command == RESPONSE

    blueiris_api.blueiris_json_logout(test_session, test_session_id)


def test_blueiris_clip(mocker: MockFixture):
    test_alert_clip = "alertclip"

    command_sec = {
        "data": [{"file": test_alert_clip, "path": "path", "filesize": "1sec"}]
    }
    command_m = {
        "data": [{"file": test_alert_clip, "path": "path", "filesize": "1m30s"}]
    }

    blueiris_command_mock = mocker.patch(
        "blueiris_alerts.server.blueiris.blueiris_clip.blueiris_api"
    )
    blueiris_command_mock.blueiris_json_login.return_value = "session", "session_id"
    blueiris_command_mock.return_value.blueiris_json_logout

    blueiris_command_mock.blueiris_command.return_value = command_sec
    blueiris_clip.get_clip(test_alert_clip)

    blueiris_command_mock.blueiris_command.return_value = command_m
    blueiris_clip.get_clip(test_alert_clip)


def test_gen_clip(mocker: MockFixture):
    test_clips = [b"content1", b"content2", False]

    expected_prefix = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
    expected_output_loop = [
        expected_prefix + b"content1" + b"\r\n",
        expected_prefix + b"content2" + b"\r\n",
    ]

    expected_output = [expected_prefix + b"content3" + b"\r\n"]

    urllib_mock = mocker.patch("blueiris_alerts.server.blueiris.blueiris_clip.urlopen")
    urllib_mock.return_value.read.return_value = b"content3"

    clip_images_mock = mocker.patch(
        "blueiris_alerts.server.blueiris.blueiris_clip.get_clip_images"
    )
    clip_images_mock.return_value = [False]

    test_gen_clip = blueiris_clip.gen_clip("path", 400)
    assert list(test_gen_clip) == expected_output

    clip_images_mock = mocker.patch(
        "blueiris_alerts.server.blueiris.blueiris_clip.get_clip_images"
    )
    clip_images_mock.return_value = test_clips

    test_gen_clip_loop = blueiris_clip.gen_clip("path", 200)
    assert list(test_gen_clip_loop) == expected_output_loop


def test_get_clip_images():
    test_clip_images = blueiris_clip.get_clip_images()
    assert test_clip_images == []


# ---------------------------------------------------------------------------
# Failure / error paths
# ---------------------------------------------------------------------------

def test_blueiris_api_login_failure(mocker):
    """Failed login response raises BlueIrisError."""
    session_post_mock = mocker.patch("requests.Session.post")
    session_post_mock.return_value.status_code = 200
    session_post_mock.return_value.json.return_value = {"result": "fail", "session": "session"}
    with pytest.raises(BlueIrisError):
        blueiris_api.blueiris_json_login()


def test_blueiris_api_command_failure(mocker):
    """Non-success command response raises BlueIrisError."""
    import requests
    session_post_mock = mocker.patch("requests.Session.post")
    session_post_mock.return_value.status_code = 200
    session_post_mock.return_value.json.return_value = {"result": "fail"}
    session = requests.Session()
    with pytest.raises(BlueIrisError):
        blueiris_api.blueiris_command(session, "session_id", "cmd", "options")


def test_blueiris_camconfig_invalid_duration():
    """Unknown duration string raises BlueIrisAlertsException."""
    with pytest.raises(BlueIrisAlertsException):
        blueiris_camconfig.convert_pause_duration("invalid_duration")


def test_blueiris_clip_not_found(mocker):
    """Empty alert list raises BlueIrisError."""
    api_mock = mocker.patch("blueiris_alerts.server.blueiris.blueiris_clip.blueiris_api")
    api_mock.blueiris_json_login.return_value = ("session", "session_id")
    api_mock.blueiris_command.return_value = {"data": []}
    with pytest.raises(BlueIrisError):
        blueiris_clip.get_clip("nonexistent.jpg")
