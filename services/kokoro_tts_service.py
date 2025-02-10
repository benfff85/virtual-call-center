import logging

from kokoro import KPipeline
import soundfile as sf

from utilities.logging_utils import configure_logger

logger = configure_logger('kokoro_tts_service_logger', logging.INFO)
pipeline = KPipeline(lang_code='a')

def generate_audio_file_from_text(text_to_speak: str) -> str:

    logger.info("Processing tts")
    generator = pipeline(
        text_to_speak, voice='af_heart', # <= change voice here
        speed=1, split_pattern="*****"
    )
    for i, (gs, ps, audio) in enumerate(generator):
        logger.info(f"Generating text to speach {i} --- {text_to_speak}")
        # TODO add support for callid and sequence
        sf.write(f'{i}.wav', audio, 24000) # save each audio file
        logger.info(f"Audio saved to {i}.wav")
    return f'{i}.wav'