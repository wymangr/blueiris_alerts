import pytest

from blueiris_alerts.server.slack import messages
from tests.test_data import TEST_BLOCKS, ALERTING_CAMERA, PATH
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.schemas import slack_schema

SETTINGS = get_settings("client")


@pytest.fixture
def setup_request_post(mocker):
    session_post_mock = mocker.patch("requests.post")
    session_post_mock.return_value.status_code = 200
    return session_post_mock


def test_response_url_post(setup_request_post):
    actions = ["pause", "start"]

    for action in actions:
        messages.response_url_post(
            action,
            TEST_BLOCKS,
            ALERTING_CAMERA,
            ALERTING_CAMERA,
            PATH,
            SETTINGS.encryption_password,
            "https://response_url",
        )
        assert setup_request_post.called


def test_update_blocks_pause():
    PAUSE = messages.update_blocks_pause(
        "pause",
        TEST_BLOCKS,
        ALERTING_CAMERA,
        ALERTING_CAMERA,
        PATH,
        SETTINGS.encryption_password,
    )
    assert PAUSE[4]["elements"][0]["text"]["text"] == "Start"
    assert PAUSE[5]["elements"][0]["placeholder"]["text"] == "Increase Pause"
    assert PAUSE[5]["elements"][0]["options"][0]["text"]["text"] == "Add 30m"

    ADD = messages.update_blocks_pause(
        "add",
        slack_schema.MessageSchema(blocks=PAUSE).blocks,
        ALERTING_CAMERA,
        ALERTING_CAMERA,
        PATH,
        SETTINGS.encryption_password,
    )
    assert ADD[5]["elements"][0]["options"][0]["text"]["text"] == "Add 30m"
    assert "CAMERA,add,1800," in ADD[5]["elements"][0]["options"][0]["value"]

    START = messages.update_blocks_pause(
        "start",
        slack_schema.MessageSchema(blocks=ADD).blocks,
        ALERTING_CAMERA,
        ALERTING_CAMERA,
        PATH,
        SETTINGS.encryption_password,
    )
    assert (
        START[3]["text"]["text"]
        == f"Pause the {ALERTING_CAMERA} camera for another 30 min?"
    )
    assert START[4]["elements"][0]["placeholder"]["text"] == "Pause"
