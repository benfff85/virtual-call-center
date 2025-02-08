from pydantic import BaseModel
from typing import Optional

class AudioData(BaseModel):
    raw_audio: str  # Raw audio bytes
    format: str  # e.g., "WAV", "MP3", "PCM"
    frequency: int  # Sampling frequency in Hz
    channels: Optional[int] = 1  # Number of audio channels
    bit_depth: Optional[int] = 16  # Bits per sample