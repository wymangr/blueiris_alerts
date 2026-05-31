import asyncio
import hashlib
import hmac
import time as _time
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from pydantic import Json

from blueiris_alerts.schemas.slack_schema import SlackInteractivity
from blueiris_alerts.server.settings import SETTINGS, BI_LOGGER
from blueiris_alerts.utils.key import encode
from blueiris_alerts.server.slack.messages import response_url_post
from blueiris_alerts.server.blueiris.blueiris_camconfig import pause
from blueiris_alerts.server.slack.pause_timer import pause_timer_task

router = APIRouter(prefix="/blueiris_alerts", tags=["slack"])

# Maps camera short name to its running pause timer Task
_pause_tasks: Dict[str, asyncio.Task] = {}


async def _verify_slack_signature(request: Request):
    """Verify the X-Slack-Signature HMAC-SHA256 header.

    Skipped (with a warning) when SLACK_SIGNING_SECRET is not configured so
    that existing deployments keep working during the migration period.
    """
    if not SETTINGS.slack_signing_secret:
        BI_LOGGER.warning(
            "SLACK_SIGNING_SECRET not configured; skipping request signature verification"
        )
        return

    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    try:
        if abs(_time.time() - int(timestamp)) > 300:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.body()
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    computed = "v0=" + hmac.new(
        SETTINGS.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/interactivity")
async def interactivity(
    payload: Annotated[Json[SlackInteractivity], Form()],
    _: Annotated[None, Depends(_verify_slack_signature)],
):
    BI_LOGGER.debug(f"/interactivity - payload: {payload}")
    if (
        payload.actions[0].type == "button"
        and payload.actions[0].text is not None
        and payload.actions[0].text.text == "View Live Feed"
    ):
        return

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

    if encode(SETTINGS.encryption_password, button_selection[3]) != button_selection[4]:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
            button_selection[3],
            button_selection[4],
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
                button_selection[3],
                button_selection[4],
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
            button_selection[3],
            button_selection[4],
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
            button_selection[3],
            button_selection[4],
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
                button_selection[3],
                button_selection[4],
                _pause_tasks,
            )
        )
        _pause_tasks[camera] = task

    return {"status": "success"}
