import asyncio
from unittest.mock import MagicMock, patch

from blueiris_alerts.server.slack.messages import update_blocks_pause
from blueiris_alerts.server.slack.pause_timer import pause_timer_task
from blueiris_alerts.tests.test_data import TEST_BLOCKS, ALERTING_CAMERA

# Build the paused-state block list (dicts) that pause_timer_task receives.
PAUSED_BLOCKS = update_blocks_pause(
    "pause", TEST_BLOCKS, ALERTING_CAMERA, ALERTING_CAMERA
)


async def _fake_to_thread(func, *args, **kwargs):
    """Drop-in for asyncio.to_thread: runs lambda calls inline; returns MagicMock for others."""
    if not args and not kwargs:
        return func()  # conversations_history lambda
    return MagicMock()  # chat_update, etc.


def test_pause_timer_task_expiry():
    """pause_sec=0 → while condition immediately false → natural expiry cleanup fires."""
    active_tasks = {ALERTING_CAMERA: MagicMock()}
    mock_client = MagicMock()
    mock_client.conversations_history.return_value.data = {
        "messages": [{"blocks": PAUSED_BLOCKS}]
    }

    with (
        patch("blueiris_alerts.server.slack.pause_timer.slack.WebClient", return_value=mock_client),
        patch("asyncio.to_thread", _fake_to_thread),
        patch("blueiris_alerts.server.slack.pause_timer.update_blocks_pause", return_value=[]),
    ):
        asyncio.run(
            pause_timer_task(
                "ts", ALERTING_CAMERA, ALERTING_CAMERA, "channel", 0, active_tasks
            )
        )

    assert ALERTING_CAMERA not in active_tasks


def test_pause_timer_task_cancelled():
    """CancelledError during sleep → camera removed from active_tasks, returns cleanly."""
    active_tasks = {ALERTING_CAMERA: MagicMock()}
    mock_client = MagicMock()
    mock_client.conversations_history.return_value.data = {
        "messages": [{"blocks": PAUSED_BLOCKS}]
    }

    async def fake_sleep(_secs):
        raise asyncio.CancelledError()

    with (
        patch("blueiris_alerts.server.slack.pause_timer.slack.WebClient", return_value=mock_client),
        patch("asyncio.to_thread", _fake_to_thread),
        patch("asyncio.sleep", fake_sleep),
    ):
        asyncio.run(
            pause_timer_task(
                "ts", ALERTING_CAMERA, ALERTING_CAMERA, "channel", 3600, active_tasks
            )
        )

    assert ALERTING_CAMERA not in active_tasks
