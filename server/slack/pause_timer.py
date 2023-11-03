import sys
import time
import os

from datetime import datetime, timedelta
import slack_sdk as slack

from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.schemas.slack_schema import MessageSchema
from blueiris_alerts.server.slack.messages import update_blocks_pause

SETTINGS = get_settings("server")
password = "secret"

if __name__ == "__main__":
    message_ts = sys.argv[1]
    camera = sys.argv[2]
    channel = sys.argv[3]
    pause_sec = int(sys.argv[4])

    timer_pid = os.getpid()
    clear_time = datetime.now() + timedelta(seconds=pause_sec)
    client = slack.WebClient(token=SETTINGS.slack_api_token)
    message = client.conversations_history(
        channel=channel, latest=message_ts, count=1, inclusive="true"
    ).data["messages"][0]
    blocks = MessageSchema(blocks=message["blocks"])

    pause_values = blocks.blocks[4].elements[0].value.split(",")
    path = pause_values[2]
    key = pause_values[3]

    while clear_time > datetime.now():
        seconds = int((clear_time - datetime.now()).seconds)
        minutes = int(seconds / 60)

        blocks.blocks[4].elements[0].text.text = f"Start ({minutes} min)"
        blocks.blocks[4].elements[0].value = f"start,0,{path},{key},{timer_pid}"
        blocks.blocks[5].elements[0].options[
            0
        ].value = f"add,{1800+seconds},{path},{key},{timer_pid}"
        blocks.blocks[5].elements[0].options[
            1
        ].value = f"add,{3600+seconds},{path},{key},{timer_pid}"
        blocks.blocks[5].elements[0].options[
            2
        ].value = f"add,{21600+seconds},{path},{key},{timer_pid}"

        client.chat_update(
            channel=channel,
            blocks=blocks.model_dump(exclude_none=True)["blocks"],
            ts=message_ts,
            text="updated",
        )
        time.sleep(60)
    new_blocks = update_blocks_pause("start", blocks.blocks, camera, path, key)

    client.chat_update(
        channel=channel,
        blocks=blocks.model_dump(exclude_none=True)["blocks"],
        ts=message_ts,
        text="updated",
    )
