import asyncio
import hashlib
import hmac as _hmac
import time
import urllib.parse
import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pytest_mock import MockFixture
from unittest.mock import MagicMock

from blueiris_alerts.server.app import app
from blueiris_alerts.server.routes import slack_routes as routes_module
from blueiris_alerts.utils.key import encode
from blueiris_alerts.schemas import slack_schema
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.tests import test_data

SETTINGS = get_settings("server")

CHANNEL = slack_schema.ChannelInteractivity(id="id")
# MESSAGE includes a View Recording button at [1] so the server can extract
# path/key for auth from the recording URL.
MESSAGE = slack_schema.MessageSchema(
    blocks=[
        slack_schema.DividerBlock(),
        slack_schema.ActionBlock(
            elements=[
                slack_schema.Elements(
                    type="button",
                    text=slack_schema.Text(text="View Recording"),
                    url=test_data.RECORDING_URL,
                )
            ]
        ),
    ],
    ts="12345.67890",
)
LIVEFEED_ACTIONS = [{"type": "button", "text": {"text": "View Live Feed"}}]


def get_button_actions(button_action: str) -> list:
    actions = [
        {
            "type": "static_select",
            "text": {"text": "text"},
            "selected_option": {
                "text": {"text": "text"},
                "value": f"camera,{button_action},1800",
            },
            "action_id": "camera",
        }
    ]
    return actions


def get_button_action_button(button_action: str) -> list:
    """Returns a 'button' type action (non-livefeed) to exercise the else branch."""
    return [
        {
            "type": "button",
            "text": {"text": "other"},
            "value": f"camera,{button_action},1800",
            "action_id": "camera",
        }
    ]


def compute_slack_sig(secret: str, timestamp: str, body: str) -> str:
    sig_base = f"v0:{timestamp}:{body}"
    return "v0=" + _hmac.new(secret.encode(), sig_base.encode(), hashlib.sha256).hexdigest()


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
        timer_mock = mocker.patch(
            "blueiris_alerts.server.routes.slack_routes.pause_timer_task",
        )

        def _close_coro(coro):
            coro.close()

        create_task_mock = mocker.patch(
            "blueiris_alerts.server.routes.slack_routes.asyncio.create_task",
            side_effect=_close_coro,
        )

        action = get_button_actions(button_option)
        data = {"payload": get_payload(action).model_dump_json()}
        response = client.post(
            "blueiris_alerts/interactivity", data=data, headers=headers
        )
        pause_mock.assert_called_once()
        response_url_post_mock.assert_called_once()
        if button_option in ("pause", "add"):
            timer_mock.assert_called_once()
            create_task_mock.assert_called_once()
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Slack signature verification
# ---------------------------------------------------------------------------


def test_slack_signature_valid(mocker: MockFixture):
    """Correctly signed request -> _verify_slack_signature returns without raising."""
    secret = "test_signing_secret"
    timestamp = str(int(time.time()))
    payload_str = "test_body"
    body = urllib.parse.urlencode({"payload": payload_str})
    sig = compute_slack_sig(secret, timestamp, body)

    mock_req = MagicMock()
    mock_req.headers = {"X-Slack-Request-Timestamp": timestamp, "X-Slack-Signature": sig}

    mocker.patch.object(routes_module.SETTINGS, "slack_signing_secret", secret)
    routes_module._verify_slack_signature(mock_req, payload_str)


def test_slack_signature_expired_timestamp(client: TestClient, headers: dict, mocker: MockFixture):
    """Timestamp > 300s old -> 401."""
    mocker.patch.object(routes_module.SETTINGS, "slack_signing_secret", "test_secret")
    old_ts = str(int(time.time()) - 400)
    data = {"payload": get_payload(LIVEFEED_ACTIONS).model_dump_json()}
    sig_headers = {**headers, "X-Slack-Request-Timestamp": old_ts, "X-Slack-Signature": "v0=invalid"}
    response = client.post("blueiris_alerts/interactivity", data=data, headers=sig_headers)
    assert response.status_code == 401


def test_slack_signature_non_numeric_timestamp(client: TestClient, headers: dict, mocker: MockFixture):
    """Non-numeric timestamp (ValueError) -> 401."""
    mocker.patch.object(routes_module.SETTINGS, "slack_signing_secret", "test_secret")
    data = {"payload": get_payload(LIVEFEED_ACTIONS).model_dump_json()}
    sig_headers = {**headers, "X-Slack-Request-Timestamp": "not_a_number", "X-Slack-Signature": "v0=invalid"}
    response = client.post("blueiris_alerts/interactivity", data=data, headers=sig_headers)
    assert response.status_code == 401


def test_slack_signature_mismatch(mocker: MockFixture):
    """Valid timestamp but wrong signature -> HTTPException(401)."""
    secret = "test_secret"
    timestamp = str(int(time.time()))
    body = urllib.parse.urlencode({"payload": "body"})
    mock_req = MagicMock()
    mock_req.headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": "v0=invalidsig",
    }
    mocker.patch.object(routes_module.SETTINGS, "slack_signing_secret", secret)
    with pytest.raises(HTTPException) as exc_info:
        routes_module._verify_slack_signature(mock_req, "body")
    assert exc_info.value.status_code == 401


def test_slack_interactivity_unauthorized(client: TestClient, headers: dict):
    """Tampered recording URL (key does not match path) -> 401."""
    bad_message = slack_schema.MessageSchema(
        blocks=[
            slack_schema.DividerBlock(),
            slack_schema.ActionBlock(
                elements=[
                    slack_schema.Elements(
                        type="button",
                        text=slack_schema.Text(text="View Recording"),
                        url="https://server/blueiris_alerts/clips?alert=some_path&key=WRONGKEY",
                    )
                ]
            ),
        ],
        ts="12345.67890",
    )
    payload = slack_schema.SlackInteractivity(
        type="type",
        actions=get_button_actions("pause"),
        channel=CHANNEL,
        message=bad_message,
        response_url="response_url",
    )
    data = {"payload": payload.model_dump_json()}
    response = client.post("blueiris_alerts/interactivity", data=data, headers=headers)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Button type (non-livefeed) -> exercises the else branch for value parsing
# ---------------------------------------------------------------------------


def test_slack_interactivity_button_type_action(client: TestClient, headers: dict, mocker: MockFixture):
    """Non-livefeed 'button' action uses payload.actions[0].value (else branch)."""
    mocker.patch("blueiris_alerts.server.routes.slack_routes.pause")
    mocker.patch("blueiris_alerts.server.routes.slack_routes.response_url_post")

    data = {"payload": get_payload(get_button_action_button("start")).model_dump_json()}
    response = client.post("blueiris_alerts/interactivity", data=data, headers=headers)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Cancel-existing-task branches
# ---------------------------------------------------------------------------


def test_slack_interactivity_start_cancels_task(client: TestClient, headers: dict, mocker: MockFixture):
    """'start' action cancels an existing pause task in _pause_tasks."""
    mock_task = MagicMock(spec=asyncio.Task)
    routes_module._pause_tasks["camera"] = mock_task
    try:
        mocker.patch("blueiris_alerts.server.routes.slack_routes.pause")
        mocker.patch("blueiris_alerts.server.routes.slack_routes.response_url_post")

        data = {"payload": get_payload(get_button_actions("start")).model_dump_json()}
        response = client.post("blueiris_alerts/interactivity", data=data, headers=headers)

        assert response.status_code == 200
        mock_task.cancel.assert_called_once()
    finally:
        routes_module._pause_tasks.pop("camera", None)


def test_slack_interactivity_add_cancels_task(client: TestClient, headers: dict, mocker: MockFixture):
    """'add' action cancels existing pause task before creating a replacement."""
    mock_task = MagicMock(spec=asyncio.Task)
    routes_module._pause_tasks["camera"] = mock_task
    try:
        mocker.patch("blueiris_alerts.server.routes.slack_routes.pause")
        mocker.patch("blueiris_alerts.server.routes.slack_routes.response_url_post")
        mocker.patch("blueiris_alerts.server.routes.slack_routes.pause_timer_task")

        def _close_coro(coro):
            coro.close()

        mocker.patch(
            "blueiris_alerts.server.routes.slack_routes.asyncio.create_task",
            side_effect=_close_coro,
        )

        data = {"payload": get_payload(get_button_actions("add")).model_dump_json()}
        response = client.post("blueiris_alerts/interactivity", data=data, headers=headers)

        assert response.status_code == 200
        mock_task.cancel.assert_called_once()
    finally:
        routes_module._pause_tasks.pop("camera", None)
