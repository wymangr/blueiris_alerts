import asyncio
import hashlib
import hmac
import time as _time
import urllib.parse
from typing import Annotated, Dict, Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, Response
from pydantic import Json

from blueiris_alerts.schemas.slack_schema import ActionBlock, SlackInteractivity
from blueiris_alerts.server.settings import SETTINGS, BI_LOGGER
from blueiris_alerts.utils.key import encode
from blueiris_alerts.server.slack.messages import response_url_post
from blueiris_alerts.server.blueiris.blueiris_camconfig import pause
from blueiris_alerts.server.slack.pause_timer import pause_timer_task

router = APIRouter(prefix="/blueiris_alerts", tags=["slack"])

# Maps camera short name to its running pause timer Task
_pause_tasks: Dict[str, asyncio.Task] = {}


def _extract_path_key(blocks) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract the alert path, expiry timestamp, and HMAC key from the
    recording URL in blocks[1].

    The recording URL has the form:
        {server_url}/blueiris_alerts/clips?alert={path}&expires={ts}&key={hmac}
    It is set once when the alert is posted and never modified, so it is
    the stable source of truth for authentication across all interactions.
    """
    try:
        recording_block = blocks[1]
        if not isinstance(recording_block, ActionBlock):
            return None, None, None
        url = recording_block.elements[0].url
        if not url:
            return None, None, None
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        return (
            params.get("alert", [None])[0],
            params.get("expires", [None])[0],
            params.get("key", [None])[0],
        )
    except (IndexError, AttributeError):
        return None, None, None


def _verify_slack_signature(
    request: Request,
    payload: Annotated[Optional[str], Form()] = None,
):
    """Verify the X-Slack-Signature HMAC-SHA256 header.

    Reconstructs the raw body from the already-parsed Form field instead of
    calling request.body() (which would fail because the Form parser has
    already consumed the stream).
    """
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    try:
        if abs(_time.time() - int(timestamp)) > 300:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Re-build the raw form body that Slack originally signed.
    raw_body = urllib.parse.urlencode({"payload": payload or ""})
    sig_basestring = f"v0:{timestamp}:{raw_body}"
    computed = "v0=" + hmac.new(
        SETTINGS.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _process_action(
    payload: SlackInteractivity,
    action: str,
    camera: str,
    camera_full: str,
    button_selection: list,
):
    """Performs the slow work (BlueIris API + Slack response_url) after 200 is
    already on its way back to Slack.  Runs as a FastAPI BackgroundTask."""
    try:
        if action == "pause":
            BI_LOGGER.info(f"/interactivity - Pausing Camera {camera}")
            assert payload.actions[0].selected_option is not None
            await asyncio.to_thread(
                pause, "pause", camera, payload.actions[0].selected_option.text.text
            )
            await asyncio.to_thread(
                response_url_post,
                action,
                payload.message.blocks,
                camera,
                camera_full,
                payload.response_url,
            )
            assert payload.message.ts is not None
            task = asyncio.create_task(
                pause_timer_task(
                    payload.message.ts,
                    camera,
                    camera_full,
                    payload.channel.id,
                    int(button_selection[2]),
                    _pause_tasks,
                )
            )
            _pause_tasks[camera] = task

        elif action == "start":
            BI_LOGGER.info(f"/interactivity - Starting Camera {camera}")
            await asyncio.to_thread(pause, "start", camera)
            await asyncio.to_thread(
                response_url_post,
                action,
                payload.message.blocks,
                camera,
                camera_full,
                payload.response_url,
            )
            existing = _pause_tasks.pop(camera, None)
            if existing:
                existing.cancel()

        elif action == "add":
            BI_LOGGER.info(f"/interactivity - Adding Pause to Camera {camera}")
            assert payload.actions[0].selected_option is not None
            await asyncio.to_thread(
                pause, "pause", camera, payload.actions[0].selected_option.text.text
            )
            await asyncio.to_thread(
                response_url_post,
                action,
                payload.message.blocks,
                camera,
                camera_full,
                payload.response_url,
            )
            existing = _pause_tasks.pop(camera, None)
            if existing:
                existing.cancel()
            assert payload.message.ts is not None
            task = asyncio.create_task(
                pause_timer_task(
                    payload.message.ts,
                    camera,
                    camera_full,
                    payload.channel.id,
                    int(button_selection[2]),
                    _pause_tasks,
                )
            )
            _pause_tasks[camera] = task
    except Exception as e:
        BI_LOGGER.error(
            f"_process_action failed for camera={camera}, action={action}: {e}",
            exc_info=True,
        )


@router.post("/interactivity")
async def interactivity(
    payload: Annotated[Json[SlackInteractivity], Form()],
    background_tasks: BackgroundTasks,
    _: Annotated[None, Depends(_verify_slack_signature)],
):
    BI_LOGGER.debug(f"/interactivity - payload: {payload}")
    if payload.actions[0].type == "button" and payload.actions[0].text is not None:
        if payload.actions[0].text.text in ("View Live Feed", "View Recording"):
            return Response(status_code=200)

    if payload.actions[0].type == "static_select":
        assert payload.actions[0].selected_option is not None
        assert payload.actions[0].selected_option.value is not None
        button_selection = payload.actions[0].selected_option.value.split(",")
    else:
        assert payload.actions[0].value is not None
        button_selection = payload.actions[0].value.split(",")
    BI_LOGGER.debug(f"/interactivity - button_selection: {button_selection}")

    action = button_selection[1]
    camera = payload.actions[0].action_id
    assert camera is not None, "action_id is required"
    camera_full = button_selection[0]

    # Auth: verify the HMAC in the recording URL rather than the button value.
    # The recording URL (blocks[1]) is signed at alert-send time and never changes.
    path, expires, key = _extract_path_key(payload.message.blocks)
    if (
        not path
        or not expires
        or not key
        or not hmac.compare_digest(
            encode(SETTINGS.encryption_password, f"{path}:{expires}"), key
        )
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    background_tasks.add_task(
        _process_action, payload, action, camera, camera_full, button_selection
    )
    return Response(status_code=200)


    return {"status": "success"}
