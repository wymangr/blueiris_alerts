import pytest

from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from blueiris_alerts.server.app import app
from blueiris_alerts.utils.key import encode
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.tests import test_data

SETTINGS = get_settings("server")
REFERER = "android-app://com.slack/"
BAD_REFERER = "https://badreferer"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def headers() -> dict:
    return {"referer": REFERER}


@pytest.fixture
def badheaders() -> dict:
    return {"referer": BAD_REFERER}


@pytest.fixture
def key() -> str:
    return encode(SETTINGS.encryption_password, test_data.PATH)


def mock_clip_content():
    t = [b"test1", b"test2"]
    for te in t:
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + te + b"\r\n")


def test_clips(client: TestClient, headers: dict, key: str, mocker: MockFixture):
    get_clip_mock = mocker.patch(
        "blueiris_alerts.server.routes.blueiris_routes.get_clip"
    )
    get_clip_mock.return_value = mock_clip_content()

    path = f"/blueiris_alerts/clips?alert={test_data.PATH}&key={key}"
    response = client.get(path, headers=headers)

    get_clip_mock.assert_called_once()
    assert response.status_code == 200


def test_live_feed(client: TestClient, headers: dict, key: str, mocker: MockFixture):
    live_feed_redirect_url = "https://redirect_url"
    get_blueiris_auth_url_mock = mocker.patch(
        "blueiris_alerts.server.routes.blueiris_routes.get_blueiris_auth_url"
    )
    get_blueiris_auth_url_mock.return_value = live_feed_redirect_url

    path = f"/blueiris_alerts/live_feed?alert={test_data.PATH}&key={key}&camera=test"
    response = client.get(path, headers=headers)

    get_blueiris_auth_url_mock.assert_called_once()
    assert response.url == live_feed_redirect_url


def test_clips_bad_ref(
    client: TestClient,
    badheaders: dict,
    key: str,
):
    path = f"/blueiris_alerts/clips?alert={test_data.PATH}&key={key}"
    response = client.get(path, headers=badheaders)

    assert response.status_code == 401


def test_live_feed_bad_ref(client: TestClient, badheaders: dict, key: str):
    path = f"/blueiris_alerts/live_feed?alert={test_data.PATH}&key={key}&camera=test"
    response = client.get(path, headers=badheaders)

    assert response.status_code == 401


def test_clips_bad_key(client: TestClient, headers: dict):
    path = f"/blueiris_alerts/clips?alert={test_data.PATH}&key=w6TDhsOmw6fDq8OUw6XDmA=="
    response = client.get(path, headers=headers)

    assert response.status_code == 401


def test_live_feed_bad_key(client: TestClient, headers: dict):
    path = f"/blueiris_alerts/clips?alert={test_data.PATH}&key=w6TDhsOmw6fDq8OUw6XDmA=="
    response = client.get(path, headers=headers)

    assert response.status_code == 401
