from pydantic import BaseModel
from typing import Callable
from schemas.audio_data import AudioData

class ConversationSegment(BaseModel):

    call_id: str
    customer_audio: AudioData
    callback: Callable[[str], None]