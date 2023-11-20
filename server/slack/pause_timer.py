import sys
import time
import os

from datetime import datetime, timedelta
import slack_sdk as slack

from blueiris_alerts.server.settings import SETTINGS, LOGGER
from blueiris_alerts.schemas.slack_schema import MessageSchema
from blueiris_alerts.server.slack.messages import update_blocks_pause


if __name__ == "__main__":
    message_ts = sys.argv[1]
    camera = sys.argv[2]
    camera_full = sys.argv[3]
    channel = sys.argv[4]
    pause_sec = int(sys.argv[5])
    LOGGER.debug(
        f"pause_timer - message_ts: {message_ts}, camera {camera}, camera_full: {camera_full}, channel: {channel}, pause_sec: {pause_sec}"
    )

    timer_pid = os.getpid()
    LOGGER.info(f"Starting pause timer with pid: {timer_pid}")

    clear_time = datetime.now() + timedelta(seconds=pause_sec)
    client = slack.WebClient(token=SETTINGS.slack_api_token)
    message = client.conversations_history(
        channel=channel, latest=message_ts, count=1, inclusive="true"
    ).data["messages"][0]
    blocks = MessageSchema(blocks=message["blocks"])

    pause_values = blocks.blocks[4].elements[0].value.split(",")
    path = pause_values[3]
    key = pause_values[4]

    while clear_time > datetime.now():
        seconds = int((clear_time - datetime.now()).seconds)
        minutes = int(seconds / 60)

        blocks.blocks[4].elements[0].text.text = f"Start ({minutes} min)"
        blocks.blocks[4].elements[
            0
        ].value = f"{camera_full},start,0,{path},{key},{timer_pid}"
        blocks.blocks[5].elements[0].options[
            0
        ].value = f"{camera_full},add,{1800+seconds},{path},{key},{timer_pid}"
        blocks.blocks[5].elements[0].options[
            1
        ].value = f"{camera_full},add,{3600+seconds},{path},{key},{timer_pid}"
        blocks.blocks[5].elements[0].options[
            2
        ].value = f"{camera_full},add,{21600+seconds},{path},{key},{timer_pid}"

        client.chat_update(
            channel=channel,
            blocks=blocks.model_dump(exclude_none=True)["blocks"],
            ts=message_ts,
            text="updated",
        )
        time.sleep(60)
    new_blocks = update_blocks_pause(
        "start", blocks.blocks, camera, camera_full, path, key
    )

    client.chat_update(
        channel=channel,
        blocks=blocks.model_dump(exclude_none=True)["blocks"],
        ts=message_ts,
        text="updated",
    )
