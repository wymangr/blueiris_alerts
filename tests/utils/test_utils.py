import pytest

from blueiris_alerts.utils import utils
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.exceptions import BlueIrisAlertsException


def test_get_blueiris_auth_url():
    test_url = "testurl.com"
    https_test = utils.get_blueiris_auth_url(
        f"https://{test_url}", "user", "password", "/test"
    )
    assert https_test == f"https://user:password@{test_url}/test"

    http_test = utils.get_blueiris_auth_url(
        f"http://{test_url}", "user", "password", "/test"
    )
    assert http_test == f"http://user:password@{test_url}/test"

    with pytest.raises(Exception) as excinfo:
        utils.get_blueiris_auth_url(f"{test_url}", "user", "password", "/test")

        assert (
            str(excinfo.value) == "blueiris_web_url needs to be a http or https address"
        )


def test_get_settings_invalid():
    """Invalid setting name raises BlueIrisAlertsException."""
    with pytest.raises(BlueIrisAlertsException):
        get_settings("invalid")
