import logging
import numpy as np
from kokoro import KPipeline

from utilities.logging_utils import configure_logger


class KokoroTtsService:
    def __init__(self):
        self.logger = configure_logger('kokoro_tts_service_logger', logging.INFO)
        self.logger.info("Kokoro TTS service initializing...")

        self.pipeline = KPipeline(lang_code='a')

        self.logger.info("Kokoro TTS service initialized")


    def generate_audio_data_from_text(self, text_to_speak: str) -> np.ndarray:

        self.logger.info("Processing tts")
        generator = self.pipeline(text=text_to_speak, voice='af_heart', speed=1, split_pattern=r'\n+')

        audio_chunks = []
        # Process each chunk
        for _, _, audio in generator:
            audio_chunks.append(audio)

        combined_audio = np.concatenate(audio_chunks)
        self.logger.info("Completed tts")

        return combined_audio