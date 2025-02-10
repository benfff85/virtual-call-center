import logging
import os

from kokoro import KPipeline
import soundfile as sf
from pydub import AudioSegment

from utilities.logging_utils import configure_logger



class KokoroTtsService:
    def __init__(self):
        self.logger = configure_logger('kokoro_tts_service_logger', logging.INFO)
        self.logger.info("Kokoro TTS service initializing...")

        self.pipeline = KPipeline(lang_code='a')

        self.logger.info("Kokoro TTS service initialized")



    def generate_audio_file_from_text(self, text_to_speak: str) -> str:

        self.logger.info("Processing tts")
        generator = self.pipeline(text=text_to_speak, voice='af_heart', speed=1, split_pattern=r'\n+')

        chunk_paths = []
        for i, (gs, ps, audio) in enumerate(generator):
            self.logger.info(f"Generating text to speach {i} --- {text_to_speak}")
            sf.write(f'{i}.wav', audio, 24000) # save each audio file
            chunk_paths.append(f'{i}.wav')
            self.logger.info(f"Audio saved to {i}.wav")

        combined = AudioSegment.empty()
        for path in chunk_paths:
            combined += AudioSegment.from_wav(path)
            os.remove(path)

        combined.export("combined.wav", format="wav")

        return "combined.wav"