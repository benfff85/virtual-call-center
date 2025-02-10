import logging
import os

from kokoro import KPipeline
import soundfile as sf
from pydub import AudioSegment

from utilities.logging_utils import configure_logger

logger = configure_logger('kokoro_tts_service_logger', logging.INFO)
pipeline = KPipeline(lang_code='a')

def generate_audio_file_from_text(text_to_speak: str) -> str:

    logger.info("Processing tts")
    generator = pipeline(
        text_to_speak, voice='af_heart', # <= change voice here
        speed=1, split_pattern=r'\n+'
    )

    chunk_paths = []
    for i, (gs, ps, audio) in enumerate(generator):
        logger.info(f"Generating text to speach {i} --- {text_to_speak}")
        sf.write(f'{i}.wav', audio, 24000) # save each audio file
        chunk_paths.append(f'{i}.wav')
        logger.info(f"Audio saved to {i}.wav")

    combined = AudioSegment.empty()
    for path in chunk_paths:
        combined += AudioSegment.from_wav(path)
        os.remove(path)

    combined.export("combined.wav", format="wav")

    return "combined.wav"