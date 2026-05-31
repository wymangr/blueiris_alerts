import requests

from typing import List, Union, cast
from fastapi import HTTPException

from blueiris_alerts.server.settings import BI_LOGGER
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
    camera_full: str,
):
    new_blocks = None
    if action == "pause":
        cast(SelectionBlock, blocks[3]).text.text = f"Start the {camera_full} camera?"
        blocks.insert(
            4,
            ActionBlock(
                elements=[
                    Elements(
                        type="button",
                        text=Text(text="Start"),
                        value=f"{camera_full},start,0",
                        action_id=camera,
                    )
                ]
            ),
        )
        action_block_5 = cast(ActionBlock, blocks[5])
        assert action_block_5.elements[0].placeholder is not None
        action_block_5.elements[0].placeholder.text = "Increase Pause"
        blocks = update_pause_element("add", blocks, camera_full)
    elif action == "start":
        cast(SelectionBlock, blocks[3]).text.text = f"Pause the {camera_full} camera for another 30 min?"
        action_block_5 = cast(ActionBlock, blocks[5])
        assert action_block_5.elements[0].placeholder is not None
        action_block_5.elements[0].placeholder.text = "Pause"
        blocks = update_pause_element("pause", blocks, camera_full)
        blocks.pop(4)
    elif action == "add":
        blocks = update_pause_element("add", blocks, camera_full)
    new_blocks = MessageSchema(blocks=blocks)
    return new_blocks.model_dump(exclude_none=True)["blocks"]


def update_pause_element(
    update: str,
    blocks: List[
        Union[ContextBlock, ImageBlock, SelectionBlock, ActionBlock, DividerBlock]
    ],
    camera_full: str,
):
    action_block = cast(ActionBlock, blocks[5])
    assert action_block.elements[0].options is not None
    action_block.elements[0].options[0].text.text = f"{update.capitalize()} 30m"
    action_block.elements[0].options[1].text.text = f"{update.capitalize()} 1h"
    action_block.elements[0].options[2].text.text = f"{update.capitalize()} 6h"
    action_block.elements[0].options[0].value = f"{camera_full},{update},1800"
    action_block.elements[0].options[1].value = f"{camera_full},{update},3600"
    action_block.elements[0].options[2].value = f"{camera_full},{update},21600"
    return blocks


def response_url_post(
    action: str,
    blocks: List[
        Union[ContextBlock, ImageBlock, SelectionBlock, ActionBlock, DividerBlock]
    ],
    camera: str,
    camera_full: str,
    response_url: str,
):
    BI_LOGGER.debug(f"response_url_post - blocks: {blocks}")
    BI_LOGGER.debug(
        f"response_url_post - action: {action}, camera: {camera}, camera_full: {camera_full}, response_url: {response_url}"
    )

    updated_blocks = update_blocks_pause(action, blocks, camera, camera_full)

    BI_LOGGER.debug(f"response_url_post - updated blocks: {updated_blocks}")

    data = {"replace_original": "true", "text": "updated", "blocks": updated_blocks}

    r = requests.post(
        response_url, headers={"Content-type": "application/json"}, json=data
    )
    if r.status_code != 200:
        raise HTTPException(
            status_code=r.status_code, detail="Failed to update message"
        )
