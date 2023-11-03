from pydantic import BaseModel
from typing import List, Optional, Union


class DividerBlock(BaseModel):
    type: str = "divider"


class MarkdownElment(BaseModel):
    type: str = "mrkdwn"
    text: str


class ContextBlock(BaseModel):
    type: str = "context"
    elements: List[MarkdownElment]


class ImageBlock(BaseModel):
    type: str = "image"
    image_url: str
    alt_text: str


class Text(BaseModel):
    type: str = "plain_text"
    text: str
    emoji: Optional[bool] = True


class SelectionBlock(BaseModel):
    type: str
    text: Text


class Options(BaseModel):
    text: Text
    value: Optional[str] = None


class SelectedOptions(BaseModel):
    text: Text
    value: str


class Elements(BaseModel):
    type: str
    text: Optional[Text] = None
    url: Optional[str] = None
    value: Optional[str] = None
    placeholder: Optional[Text] = None
    action_id: Optional[str] = None
    action_ts: Optional[str] = None
    options: Optional[List[Options]] = None
    selected_option: Optional[SelectedOptions] = None


class ElementsValueUrl(BaseModel):
    url: Optional[str] = None
    value: Optional[str] = None


class ActionBlock(BaseModel):
    type: str = "actions"
    elements: List[Elements]


class MessageSchema(BaseModel):
    blocks: List[
        Union[ContextBlock, ImageBlock, SelectionBlock, ActionBlock, DividerBlock]
    ]
    ts: Optional[str] = None


class ChannelInteractivity(BaseModel):
    id: str


class SlackInteractivity(BaseModel):
    type: str
    actions: List[Elements]
    channel: ChannelInteractivity
    message: MessageSchema
    response_url: str
