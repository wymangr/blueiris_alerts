import pytest
import slack_sdk

from pytest_mock import MockFixture
from blueiris_alerts.client import slack_alert
from blueiris_alerts.schemas import slack_schema
from blueiris_alerts.tests import test_data

SLACK_MOCKER = "slack_sdk.WebClient"
TEST_MESSAGE = slack_schema.MessageSchema(blocks=test_data.TEST_BLOCKS)


@pytest.fixture
def slack_client() -> slack_sdk.WebClient:
    return slack_sdk.WebClient(token="xoxp-1234")


def test_watchdog_alert(mocker: MockFixture):
    slack_client_mock = mocker.patch(SLACK_MOCKER)
    slack_client_mock.return_value.chat_postMessage
    slack_alert.watchdog_alert("camera", "status", slack_client_mock)


def test_update_old(mocker: MockFixture):
    test_messages = {
        "ok": True,
        "messages": [{"ts": "ts", "blocks": TEST_MESSAGE.model_dump()["blocks"]}],
    }

    slack_client_mock = mocker.patch("slack_sdk.WebClient")
    slack_client_mock.conversations_list.return_value = {
        "channels": [{"name": "channel", "id": "id"}]
    }
    slack_client_mock.conversations_history.return_value.data = test_messages
    slack_client_mock.return_value.chat_update

    update_old = slack_alert.update_old("camera", slack_client_mock)
    assert update_old is True


def test_send_alert(mocker: MockFixture):
    slack_client_mock = mocker.patch(SLACK_MOCKER)
    slack_client_mock.return_value.chat_postMessage

    slack_alert.send_alert("camera", "camera", "path", slack_client_mock, "memo")
