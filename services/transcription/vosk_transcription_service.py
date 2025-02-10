from typing import Optional

from vosk import Model, KaldiRecognizer

from services.transcription.transcription_service import TranscriptionService
from utilities.logging_utils import configure_logger
import base64
import audioop
import logging
import json

class VoskTranscriptionService(TranscriptionService):
    def __init__(self, model_name: str):
        self.logger = configure_logger('vosk_transcription_service_logger', logging.INFO)
        self.logger.info("Vosk transcription service initializing...")

        self.recognizer = KaldiRecognizer(Model(model_name), 16000) # When set to 8000 we get "Sampling frequency mismatch, expected 16000, got 8000"

        self.logger.info("Vosk transcription service initialized")


    def process_audio(self, input_audio_data: str) -> Optional[str]:
        """Process incoming audio chunks and return transcription when appropriate."""
        audio = base64.b64decode(input_audio_data)
        pcm = audioop.ulaw2lin(audio, 2) # 8kHz u-law → 16-bit linear

        # Add explicit resampling to 16kHz
        pcm = audioop.ratecv(
            pcm,
            2,          # Sample width (2 bytes)
            1,          # Channels
            8000,       # Input rate
            16000,      # Output rate
            None
        )[0]

        if self.recognizer.AcceptWaveform(pcm):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()

            if text:
                self.logger.info("Transcribed: %s", text)
                return text
