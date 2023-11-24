import sys
import psutil
import subprocess as sp

from fastapi import APIRouter, Form, Header, HTTPException
from typing import Annotated
from pydantic import Json

from blueiris_alerts.schemas.slack_schema import SlackInteractivity
from blueiris_alerts.server.settings import SETTINGS, BI_LOGGER
from blueiris_alerts.utils.key import decode
from blueiris_alerts.server.slack.messages import response_url_post
from blueiris_alerts.server.blueiris.blueiris_camconfig import pause

router = APIRouter(prefix="/blueiris_alerts", tags=["slack"])


@router.post("/interactivity")
async def interactivity(
    payload: Annotated[Json[SlackInteractivity], Form()],
    user_agent: Annotated[str | None, Header()] = None,
):
    BI_LOGGER.debug(f"/interactivity - payload: {payload}")
    BI_LOGGER.debug(f"/interactivity - user_agent: {user_agent}")
    if (
        payload.actions[0].type == "button"
        and payload.actions[0].text.text == "View Live Feed"
    ):
        return

    if "Slackbot" not in user_agent:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if payload.actions[0].type == "static_select":
        button_selection = payload.actions[0].selected_option.value.split(",")
    else:
        button_selection = payload.actions[0].value.split(",")
    BI_LOGGER.debug(f"/interactivity - button_selection: {button_selection}")

    action = button_selection[1]
    camera = payload.actions[0].action_id
    camera_full = button_selection[0]

    if button_selection[3] != decode(SETTINGS.encryption_password, button_selection[4]):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if action == "pause":
        BI_LOGGER.info(f"/interactivity - Pausing Camera {camera}")
        pause("pause", camera, payload.actions[0].selected_option.text.text)
        response_url_post(
            action,
            payload.message.blocks,
            camera,
            camera_full,
            button_selection[3],
            button_selection[4],
            payload.response_url,
        )
        pause_sec = button_selection[2]
        sp.Popen(
            [
                sys.executable,
                "slack/pause_timer.py",
                payload.message.ts,
                camera,
                camera_full,
                payload.channel.id,
                pause_sec,
            ]
        )

    elif action == "start":
        BI_LOGGER.info(f"/interactivity - Starting Camera {camera}")
        pause("start", camera)
        response_url_post(
            action,
            payload.message.blocks,
            camera,
            camera_full,
            button_selection[3],
            button_selection[4],
            payload.response_url,
        )
        p = psutil.Process(int(button_selection[5]))
        p.terminate()

    elif action == "add":
        BI_LOGGER.info(f"/interactivity - Adding Pause to Camera {camera}")
        pause("pause", camera, payload.actions[0].selected_option.text.text)
        response_url_post(
            action,
            payload.message.blocks,
            camera,
            camera_full,
            button_selection[3],
            button_selection[4],
            payload.response_url,
        )
        pause_sec = button_selection[2]
        p = psutil.Process(int(button_selection[5]))
        p.terminate()
        sp.Popen(
            [
                sys.executable,
                "slack/pause_timer.py",
                payload.message.ts,
                camera,
                camera_full,
                payload.channel.id,
                pause_sec,
            ]
        )

    return {"status": "success"}
