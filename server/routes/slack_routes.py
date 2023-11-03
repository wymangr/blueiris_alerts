import sys
import psutil
import subprocess as sp

from fastapi import APIRouter, Form, Header, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Annotated
from pydantic import Json

from blueiris_alerts.schemas.slack_schema import SlackInteractivity
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.key import decode
from blueiris_alerts.server.blueiris.blueiris_clip import get_clip
from blueiris_alerts.server.slack.messages import response_url_post
from blueiris_alerts.server.blueiris.blueiris_camconfig import pause
from blueiris_alerts.utils.utils import get_blueiris_auth_url

router = APIRouter(prefix="/playground", tags=["slack"])

SETTINGS = get_settings("server")


@router.post("/interactivity")
async def interactivity(
    payload: Annotated[Json[SlackInteractivity], Form()],
    user_agent: Annotated[str | None, Header()] = None,
):
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
    action = button_selection[0]
    camera = payload.actions[0].action_id

    if button_selection[2] != decode(SETTINGS.encryption_password, button_selection[3]):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if action == "pause":
        pause("pause", camera, payload.actions[0].selected_option.text.text)
        response_url_post(
            action,
            payload.message.blocks,
            camera,
            button_selection[2],
            button_selection[3],
            payload.response_url,
        )
        pause_sec = button_selection[1]
        sp.Popen(
            [
                sys.executable,
                "slack/pause_timer.py",
                payload.message.ts,
                camera,
                payload.channel.id,
                pause_sec,
            ]
        )

    elif action == "start":
        pause("start", camera)
        response_url_post(
            action,
            payload.message.blocks,
            camera,
            button_selection[2],
            button_selection[3],
            payload.response_url,
        )
        p = psutil.Process(int(button_selection[4]))
        p.terminate()

    elif action == "add":
        pause("pause", camera, payload.actions[0].selected_option.text.text)
        response_url_post(
            action,
            payload.message.blocks,
            camera,
            button_selection[2],
            button_selection[3],
            payload.response_url,
        )
        pause_sec = button_selection[1]
        p = psutil.Process(int(button_selection[4]))
        p.terminate()
        sp.Popen(
            [
                sys.executable,
                "slack/pause_timer.py",
                payload.message.ts,
                camera,
                payload.channel.id,
                pause_sec,
            ]
        )

    return {"status": "success"}


@router.get("/clips")
async def clips(alert: str, key: str, referer: Annotated[str | None, Header()] = None):
    if referer != "android-app://com.slack/" or alert != decode(
        SETTINGS.encryption_password, key
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return StreamingResponse(
        get_clip(alert), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/live_feed")
async def live_feed(
    alert: str, camera: str, key: str, referer: Annotated[str | None, Header()] = None
):
    if referer != "android-app://com.slack/" or alert != decode(
        SETTINGS.encryption_password, key
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    live_feed_url = get_blueiris_auth_url(
        SETTINGS.blueiris_web_url,
        SETTINGS.blueiris_api_user,
        SETTINGS.blueiris_api_password,
    )
    return RedirectResponse(url=f"{live_feed_url}/mjpg/{camera}/video.mjpg")
