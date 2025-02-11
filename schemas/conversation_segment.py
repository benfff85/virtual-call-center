import numpy as np
from pydantic import BaseModel
from typing import Optional
from schemas.audio_data import AudioData
from schemas.conversation_input_channel_type import ConversationInputChannelType
from schemas.conversation_output_channel_type import ConversationOutputChannelType


class ConversationSegment(BaseModel):

    class Config:
        arbitrary_types_allowed = True

    call_id: str
    input_audio_channel: ConversationInputChannelType = None
    customer_audio: AudioData
    customer_text: Optional[str] = None

    output_audio_channel: ConversationOutputChannelType = None
    specialist_text: Optional[str] = None
    specialist_audio_data: Optional[np.ndarray] = None
    specialist_audio_file: Optional[str] = None
