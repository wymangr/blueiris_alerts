from blueiris_alerts.schemas import slack_schema
from blueiris_alerts.utils.config import get_settings
from blueiris_alerts.utils.key import encode

SETTINGS = get_settings("client")
ALERTING_CAMERA = "CAMERA"
PATH = "AB.20230101_000000.123456.1-1.jpg"

TEST_BLOCKS = [
    slack_schema.DividerBlock(),
    slack_schema.ContextBlock(
        elements=[slack_schema.MarkdownElment(text="https://view_recording_link")]
    ),
    slack_schema.ImageBlock(image_url="https://image_url", alt_text="alert"),
    slack_schema.SelectionBlock(
        type="section",
        text=slack_schema.Text(
            text=f"Pause the {ALERTING_CAMERA} camera for 30 min?", emoji=True
        ),
    ),
    slack_schema.ActionBlock(
        elements=[
            slack_schema.Elements(
                type="static_select",
                action_id=ALERTING_CAMERA,
                placeholder=slack_schema.Text(text="Pause"),
                options=[
                    slack_schema.Options(
                        text=slack_schema.Text(text="Pause 30m"),
                        value=f"{ALERTING_CAMERA},pause,1800,{PATH},{encode(SETTINGS.encryption_password, PATH)}",
                    ),
                    slack_schema.Options(
                        text=slack_schema.Text(text="Pause 1h"),
                        value=f"{ALERTING_CAMERA},pause,3600,{PATH},{encode(SETTINGS.encryption_password, PATH)}",
                    ),
                    slack_schema.Options(
                        text=slack_schema.Text(text="Pause 6h"),
                        value=f"{ALERTING_CAMERA},pause,21600,{PATH},{encode(SETTINGS.encryption_password, PATH)}",
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
                url="https://live_feed_url",
            )
        ]
    ),
    slack_schema.DividerBlock(),
]
