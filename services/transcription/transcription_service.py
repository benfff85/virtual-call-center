from abc import ABC, abstractmethod
from typing import Optional


class TranscriptionService(ABC):
    @abstractmethod
    def process_audio(self, input_audio_data: str) -> Optional[str]:
        """
        Process incoming audio data and return a transcription if available.
        """
        pass
