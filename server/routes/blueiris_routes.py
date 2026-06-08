import asyncio
import hmac as _hmac
import time as _time

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Annotated, Optional

from blueiris_alerts.server.settings import SETTINGS, BI_LOGGER
from blueiris_alerts.utils.key import encode
from blueiris_alerts.server.blueiris.blueiris_clip import get_clip
from blueiris_alerts.utils.utils import get_blueiris_auth_url


router = APIRouter(prefix="/blueiris_alerts", tags=["blueiris"])


def _check_auth(alert: str, expires: str, key: str) -> bool:
    """Return True if the HMAC is valid and the URL has not yet expired."""
    try:
        if int(expires) < int(_time.time()):
            return False
    except ValueError:
        return False
    return _hmac.compare_digest(
        encode(SETTINGS.encryption_password, f"{alert}:{expires}"), key
    )


def _is_slack_referer(referer: Optional[str]) -> bool:
    """Allow requests with no Referer (desktop/iOS Slack) or a Slack-origin Referer.

    Rejects only requests that carry a Referer that is clearly not Slack,
    which catches accidental URL sharing while not blocking legitimate clients.
    """
    if referer is None:
        return True
    return "slack" in referer.lower()


@router.get("/clips")
async def clips(
    alert: str,
    expires: str,
    key: str,
    referer: Annotated[Optional[str], Header()] = None,
):
    BI_LOGGER.debug(f"/clips - alert: {alert}, referer: {referer}")
    if not _is_slack_referer(referer) or not _check_auth(alert, expires, key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    generator = await asyncio.to_thread(get_clip, alert)
    return StreamingResponse(
        generator, media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/live_feed")
async def live_feed(
    alert: str,
    camera: str,
    expires: str,
    key: str,
    referer: Annotated[Optional[str], Header()] = None,
):
    BI_LOGGER.debug(
        f"/live_feed - alert: {alert}, camera: {camera}, referer: {referer}"
    )
    if not _is_slack_referer(referer) or not _check_auth(alert, expires, key):
        raise HTTPException(status_code=401, detail="Unauthorized")

    live_feed_url = get_blueiris_auth_url(
        SETTINGS.blueiris_web_url,
        SETTINGS.blueiris_api_user,
        SETTINGS.blueiris_api_password,
        f"/mjpg/{camera}/video.mjpg",
    )

    return RedirectResponse(url=live_feed_url, status_code=301)
