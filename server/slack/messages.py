import random
import requests

from typing import List, Union
from fastapi import HTTPException

from blueiris_alerts.schemas.slack_schema import (
    MessageSchema,
    ActionBlock,
    ContextBlock,
    ImageBlock,
    SelectionBlock,
    DividerBlock,
    Elements,
    Text,
)


def update_blocks_pause(
    action: str,
    blocks: List[
        Union[ContextBlock, ImageBlock, SelectionBlock, ActionBlock, DividerBlock]
    ],
    camera: str,
    path: str,
    key: str,
):
    new_blocks = None
    if action == "pause":
        blocks[3].text.text = f"Start the {camera} camera?"
        blocks.insert(
            4,
            ActionBlock(
                elements=[
                    Elements(
                        type="button",
                        text=Text(text="Start"),
                        value=f"start,0,{path},{key}",
                        action_id=camera,
                    )
                ]
            ),
        )
        blocks[5].elements[0].placeholder.text = "Increase Pause"
        blocks = update_pause_element("add", blocks, path, key)
    elif action == "start":
        blocks[3].text.text = f"Pause the {camera} camera for another 30 min?"
        blocks[5].elements[0].placeholder.text = "Pause"
        blocks = update_pause_element("pause", blocks, path, key)
        blocks.pop(4)
    elif action == "add":
        blocks = update_pause_element("add", blocks, path, key)
    new_blocks = MessageSchema(blocks=blocks)
    return new_blocks.model_dump(exclude_none=True)["blocks"]


def update_pause_element(
    update: str,
    blocks: List[
        Union[ContextBlock, ImageBlock, SelectionBlock, ActionBlock, DividerBlock]
    ],
    path: str,
    key: str,
):
    blocks[5].elements[0].options[0].text.text = f"{update.capitalize()} 30m"
    blocks[5].elements[0].options[1].text.text = f"{update.capitalize()} 1h"
    blocks[5].elements[0].options[2].text.text = f"{update.capitalize()} 6h"
    blocks[5].elements[0].options[
        0
    ].value = f"{update},1800,{path},{key},{random.randint(10,99)}"
    blocks[5].elements[0].options[
        1
    ].value = f"{update},3600,{path},{key},{random.randint(10,99)}"
    blocks[5].elements[0].options[
        2
    ].value = f"{update},21600,{path},{key},{random.randint(10,99)}"

    return blocks


def response_url_post(
    action: str,
    blocks: List[
        Union[ContextBlock, ImageBlock, SelectionBlock, ActionBlock, DividerBlock]
    ],
    camera: str,
    path: str,
    key: str,
    response_url: str,
):
    updated_blocks = update_blocks_pause(action, blocks, camera, path, key)

    data = {"replace_original": "true", "text": "updated", "blocks": updated_blocks}

    r = requests.post(
        response_url, headers={"Content-type": "application/json"}, json=data
    )
    if r.status_code != 200:
        raise HTTPException(
            status_code=r.status_code, detail="Failed to update message"
        )
