from vosk import Model, KaldiRecognizer
from utilities.logging_utils import configure_logger
import base64
import audioop
import logging
import json

logger = configure_logger('vosk_transcription_service_logger', logging.INFO)

# vosk_model = Model("vosk-model-small-en-us-0.15")
vosk_model = Model("vosk-model-en-us-0.22")

recognizer = KaldiRecognizer(vosk_model, 16000) # When set to 8000 we get "Sampling frequency mismatch, expected 16000, got 8000"

def process_audio(input_audio_data):
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

    if recognizer.AcceptWaveform(pcm):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()

        if text:
            logger.info("Transcribed: %s", text)
            return text
