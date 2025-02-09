import logging
import os

from services.transcription.whisper_transcription_service import WhisperTranscriptionService
from utilities.logging_utils import configure_logger


class TranscriptionGateway:
    def __init__(self):  # Maximum buffer size in seconds
        self.logger = configure_logger('transcription_gateway_logger', logging.INFO)
        self.logger.info("Transcription gateway initializing...")

        self.transcription_service_prop = os.getenv("TRANSCRIPTION_SERVICE", "whisper").lower()
        self.transcription_model_prop = os.getenv("TRANSCRIPTION_MODEL", "large-v3-turbo").lower()

        if self.transcription_service_prop == "whisper":
            self.logger.info(f"Using Whisper transcription service with model: {self.transcription_model_prop}")
            self.transcription_service = WhisperTranscriptionService(model_name=self.transcription_model_prop, silence_duration=1.0)
        else:
            self.logger.error(f"Unknown transcription service: {self.transcription_service_prop}")
            # TODO - Add Vosk
            # self.transcription_service = VoskTranscriptionService(model_name=self.transcription_model_prop, silence_duration=1.0)

        self.logger.info("Transcription gateway initialized")

    def transcribe(self, input_audio_data: str) -> str:
        return self.transcription_service.process_audio(input_audio_data)
