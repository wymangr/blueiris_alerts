import argparse
import paho.mqtt.client as mqtt
import slack_sdk as slack

from pydantic import ValidationError

from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.key import encode
from blueiris_alerts.utils.utils import get_blueiris_auth_url
from blueiris_alerts.schemas import slack_schema

SETTINGS = get_settings("client")


def watchdog_alert(camera: str, status: str, slack_client: slack.WebClient):
    message_text = f"The {camera} camera is {status}"
    slack_client.chat_postMessage(text=message_text, channel=SETTINGS.slack_channel)


def remove_message_blocks(removed_message_blocks: dict, channel: str):
    if removed_message_blocks:
        for message_timestamp in removed_message_blocks:
            blocks = removed_message_blocks[message_timestamp]["blocks"]
            blocks.pop(5)
            blocks.pop(4)
            blocks.pop(3)

            client.chat_update(
                channel=channel, blocks=blocks, ts=message_timestamp, text="updated"
            )


def get_channel_id(channels: dict):
    channel_id = None
    for c in channels["channels"]:
        if c["name"] == SETTINGS.slack_channel:
            channel_id = c["id"]
    return channel_id


def update_old(camera: str, slack_client: slack.WebClient):
    try:
        channels = slack_client.conversations_list()
        channel_id = get_channel_id(channels)
        if not channel_id:
            print("unable to get channel id")
            return
        messages = slack_client.conversations_history(channel=channel_id, count=10).data
        if not messages["ok"]:
            print("unable to update old messages")
            return
        removed_message_blocks = {}
        for message in messages["messages"]:
            if "blocks" in message.keys() and len(message["blocks"]) == 7:
                try:
                    message_block = slack_schema.MessageSchema(blocks=message["blocks"])
                    if (
                        message_block.blocks[4].elements[0].action_id == camera
                        and message_block.blocks[4].elements[0].placeholder.text
                        == "Pause"
                    ):
                        removed_message_blocks[
                            message["ts"]
                        ] = message_block.model_dump()
                except ValidationError:
                    print("Failed Validation")
                    continue
        remove_message_blocks(removed_message_blocks, channel_id)
    except Exception as e:
        print(e)


def auth_image_url(base_url: str, user: str, password: str, index: int):
    return f"{base_url[:index]}{user}:{password}@{base_url[index:]}"


def send_alert(camera: str, path: str, slack_client: slack.WebClient, memo: str):
    message_text = f"{camera} alert! {memo}"

    image_base_url = get_blueiris_auth_url(
        SETTINGS.blueiris_web_url,
        SETTINGS.blueiris_api_user,
        SETTINGS.blueiris_api_password,
    )
    image_url = f"{image_base_url}/file/clips/{path}"

    recording_url = f"{SETTINGS.server_url}/blueiris_alerts/clips?alert={path}&key={encode(SETTINGS.encryption_password, path)}"
    view_recording_link = f"<{recording_url}|```View Recording```>"
    live_feed_url = f"{SETTINGS.server_url}/blueiris_alerts/live_feed?alert={path}&camera={camera}&key={encode(SETTINGS.encryption_password, path)}"

    blocks = slack_schema.MessageSchema(
        blocks=[
            slack_schema.DividerBlock(),
            slack_schema.ContextBlock(
                elements=[slack_schema.MarkdownElment(text=view_recording_link)]
            ),
            slack_schema.ImageBlock(image_url=image_url, alt_text="alert"),
            slack_schema.SelectionBlock(
                type="section",
                text=slack_schema.Text(
                    text=f"Pause the {camera} camera for 30 min?", emoji=True
                ),
            ),
            slack_schema.ActionBlock(
                elements=[
                    slack_schema.Elements(
                        type="static_select",
                        action_id=camera,
                        placeholder=slack_schema.Text(text="Pause"),
                        options=[
                            slack_schema.Options(
                                text=slack_schema.Text(text="Pause 30m"),
                                value=f"pause,1800,{path},{encode(SETTINGS.encryption_password, path)}",
                            ),
                            slack_schema.Options(
                                text=slack_schema.Text(text="Pause 1h"),
                                value=f"pause,3600,{path},{encode(SETTINGS.encryption_password, path)}",
                            ),
                            slack_schema.Options(
                                text=slack_schema.Text(text="Pause 6h"),
                                value=f"pause,21600,{path},{encode(SETTINGS.encryption_password, path)}",
                            ),
                        ],
                    )
                ]
            ),
            slack_schema.ActionBlock(
                elements=[
                    slack_schema.Elements(
                        type="button",
                        text=slack_schema.Text(text="View Live Feed", emoji=True),
                        url=live_feed_url,
                    )
                ]
            ),
            slack_schema.DividerBlock(),
        ]
    )

    slack_client.chat_postMessage(
        text=message_text,
        channel=SETTINGS.slack_channel,
        blocks=blocks.model_dump(exclude_none=True)["blocks"],
        icon_url=image_url,
    )


def mqtt_message(camera: str, status: str):
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(SETTINGS.mqtt_user, SETTINGS.mqtt_pw)
        mqtt_client.connect(SETTINGS.mqtt_broker, 1883, 60)
        mqtt_client.publish(f"camera_alerts/{camera}", status)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--camera", required=True, help="Alerting Camera Short Name"
    )
    parser.add_argument(
        "-p",
        "--path",
        help="Name of Alert jpg. Can be passed in via BI Variable: `&ALERT_PATH`",
    )
    parser.add_argument(
        "-M", "--memo", help="AI memo. Can be passed in via BI Variable: `&MEMO`"
    )
    parser.add_argument(
        "-m",
        "--mqtt",
        action="store_true",
        help="Option to send motion message to MQTT server",
    )
    parser.add_argument(
        "-mr",
        "--mqtt_reset",
        action="store_true",
        help="Option to send no motion message to MQTT server. 'on reset'",
    )
    parser.add_argument(
        "-o",
        "--offline",
        action="store_true",
        help="For Watchdog alerts. Camera is Offline",
    )
    parser.add_argument(
        "-O",
        "--online",
        action="store_true",
        help="For Watchdog alerts. Camera is Online",
    )

    args = parser.parse_args()
    config = vars(args)

    alerting_camera = config["camera"]
    alert_path = config["path"]
    memo = config["memo"]
    mqtt_true = config["mqtt"]
    mqtt_reset = config["mqtt_reset"]
    offline = config["offline"]
    online = config["online"]

    client = slack.WebClient(token=SETTINGS.slack_api_token)

    if offline or online:
        assert not all((online, offline)), "Can only specify --online OR --offline"
        if offline:
            watchdog_alert(alerting_camera, "offline", client)
        elif online:
            watchdog_alert(alerting_camera, "online", client)
    elif mqtt_reset:
        assert all(
            (SETTINGS.mqtt_broker, SETTINGS.mqtt_user, SETTINGS.mqtt_password)
        ), "Missing MQTT configuration"
        mqtt_message(alerting_camera, "no_motion")
    else:
        assert alert_path is not None, "--path is required"

        update_old(alerting_camera, client)
        send_alert(alerting_camera, alert_path, client, memo)

        if mqtt_true:
            assert all(
                (SETTINGS.mqtt_broker, SETTINGS.mqtt_user, SETTINGS.mqtt_password)
            ), "Missing MQTT configuration"
            mqtt_message(alerting_camera, "motion")