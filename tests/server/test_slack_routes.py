import pytest

from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from blueiris_alerts.server.app import app
from blueiris_alerts.utils.key import encode
from blueiris_alerts.schemas import slack_schema
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.tests import test_data

SETTINGS = get_settings("server")

CHANNEL = slack_schema.ChannelInteractivity(id="id")
MESSAGE = slack_schema.MessageSchema(blocks=[slack_schema.DividerBlock()])
LIVEFEED_ACTIONS = [{"type": "button", "text": {"text": "View Live Feed"}}]


def get_button_actions(button_action: str) -> list:
    actions = [
        {
            "type": "static_select",
            "text": {"text": "text"},
            "selected_option": {
                "text": {"text": "text"},
                "value": f"camera,{button_action},1800,{test_data.PATH},{encode(SETTINGS.encryption_password, test_data.PATH)},9999",
            },
            "action_id": "camera",
        }
    ]

    return actions


def get_payload(actions: list) -> slack_schema.SlackInteractivity:
    payload = slack_schema.SlackInteractivity(
        type="type",
        actions=actions,
        channel=CHANNEL,
        message=MESSAGE,
        response_url="response_url",
    )
    return payload


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def headers() -> dict:
    return {
        "user-agent": "Slackbot",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_slack_interactivity_livefeed(client: TestClient, headers: dict):
    data = {"payload": get_payload(LIVEFEED_ACTIONS).model_dump_json()}
    response = client.post("blueiris_alerts/interactivity", data=data, headers=headers)
    assert response.status_code == 200


def test_slack_interactivity_pause(
    client: TestClient, headers: dict, mocker: MockFixture
):
    button_options = ["pause", "start", "add"]

    for button_option in button_options:
        pause_mock = mocker.patch("blueiris_alerts.server.routes.slack_routes.pause")
        response_url_post_mock = mocker.patch(
            "blueiris_alerts.server.routes.slack_routes.response_url_post"
        )
        popen_mock = mocker.patch("blueiris_alerts.server.routes.slack_routes.sp.Popen")
        process_mock = mocker.patch(
            "blueiris_alerts.server.routes.slack_routes.psutil.Process"
        )
        process_mock.return_value.terminate

        action = get_button_actions(button_option)
        data = {"payload": get_payload(action).model_dump_json()}
        response = client.post(
            "blueiris_alerts/interactivity", data=data, headers=headers
        )
        pause_mock.assert_called_once()
        response_url_post_mock.assert_called_once()
        if button_option == "pause" or button_option == "add":
            popen_mock.assert_called_once()
        if button_option == "start" or button_option == "add":
            process_mock.assert_called_once()
        assert response.status_code == 200
