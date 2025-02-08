from pydantic import BaseModel
from typing import Callable, Optional
from schemas.audio_data import AudioData

class ConversationSegment(BaseModel):

    call_id: str
    customer_audio: AudioData
    customer_text: Optional[str] = None

    specialist_text: Optional[str] = None
    callback: Callable[[str], None]