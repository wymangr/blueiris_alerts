from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Annotated

from blueiris_alerts.server.settings import SETTINGS, LOGGER
from blueiris_alerts.utils.key import decode
from blueiris_alerts.server.blueiris.blueiris_clip import get_clip
from blueiris_alerts.utils.utils import get_blueiris_auth_url


router = APIRouter(prefix="/blueiris_alerts", tags=["blueiris"])


@router.get("/clips")
async def clips(alert: str, key: str, referer: Annotated[str | None, Header()] = None):
    LOGGER.debug(f"/clips - alert: {alert}, referer: {referer}")
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
    LOGGER.debug(f"/live_feed - alert: {alert}, camera: {camera}, referer: {referer}")
    if referer != "android-app://com.slack/" or alert != decode(
        SETTINGS.encryption_password, key
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    live_feed_url = get_blueiris_auth_url(
        SETTINGS.blueiris_web_url,
        SETTINGS.blueiris_api_user,
        SETTINGS.blueiris_api_password,
        f"/mjpg/{camera}/video.mjpg",
    )

    return RedirectResponse(url=live_feed_url, status_code=301)
