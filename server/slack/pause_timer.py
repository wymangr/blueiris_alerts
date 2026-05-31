import asyncio
from datetime import datetime, timedelta
from typing import Dict, cast

import slack_sdk as slack

from blueiris_alerts.server.settings import SETTINGS, BI_LOGGER, SLACK_LOGGER
from blueiris_alerts.schemas.slack_schema import ActionBlock, MessageSchema
from blueiris_alerts.server.slack.messages import update_blocks_pause


async def pause_timer_task(
    message_ts: str,
    camera: str,
    camera_full: str,
    channel: str,
    pause_sec: int,
    path: str,
    key: str,
    active_tasks: Dict[str, asyncio.Task],
):
    """Runs as an asyncio background task.

    Updates the Slack message every 60 seconds with the remaining pause time.
    Cancels cleanly when the caller cancels the task (on "start" or "add").
    When the timer expires naturally it reverts the message to the un-paused UI.
    """
    clear_time = datetime.now() + timedelta(seconds=pause_sec)
    client = slack.WebClient(token=SETTINGS.slack_api_token, logger=SLACK_LOGGER)
    BI_LOGGER.info(f"pause_timer_task started for camera={camera}, pause_sec={pause_sec}")

    message = await asyncio.to_thread(
        lambda: cast(dict, client.conversations_history(
            channel=channel, latest=message_ts, count=1, inclusive=True
        ).data)["messages"][0]
    )
    blocks = MessageSchema(blocks=message["blocks"])

    try:
        while clear_time > datetime.now():
            seconds = int((clear_time - datetime.now()).total_seconds())
            minutes = int(seconds / 60)

            block_4 = cast(ActionBlock, blocks.blocks[4])
            block_5 = cast(ActionBlock, blocks.blocks[5])
            assert block_4.elements[0].text is not None
            assert block_5.elements[0].options is not None
            block_4.elements[0].text.text = f"Start ({minutes} min)"
            block_4.elements[0].value = f"{camera_full},start,0,{path},{key}"
            block_5.elements[0].options[0].value = (
                f"{camera_full},add,{1800 + seconds},{path},{key}"
            )
            block_5.elements[0].options[1].value = (
                f"{camera_full},add,{3600 + seconds},{path},{key}"
            )
            block_5.elements[0].options[2].value = (
                f"{camera_full},add,{21600 + seconds},{path},{key}"
            )

            await asyncio.to_thread(
                client.chat_update,
                channel=channel,
                blocks=blocks.model_dump(exclude_none=True)["blocks"],
                ts=message_ts,
                text="updated",
            )
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        BI_LOGGER.info(f"pause_timer_task cancelled for camera={camera}")
        active_tasks.pop(camera, None)
        return

    BI_LOGGER.info(f"pause_timer_task expired for camera={camera}")
    active_tasks.pop(camera, None)

    new_blocks = update_blocks_pause("start", blocks.blocks, camera, camera_full, path, key)
    await asyncio.to_thread(
        client.chat_update,
        channel=channel,
        blocks=new_blocks,
        ts=message_ts,
        text="updated",
    )
