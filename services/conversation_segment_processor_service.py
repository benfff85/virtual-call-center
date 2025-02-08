from schemas.conversation_segment import ConversationSegment
from services import kokoro_tts_service
from services.whisper_transcription_service import WhisperTranscriptionService
from utilities.logging_utils import configure_logger
import logging

logger = configure_logger('conversation_segment_processor_service_logger', logging.INFO)

transcription_service = WhisperTranscriptionService(silence_duration=1.0)

def process_conversation_segment(conversation_segment: ConversationSegment):

    # TODO convert audio format if needed

    conversation_segment.customer_text = transcription_service.process_audio(conversation_segment.customer_audio.raw_audio)
    if conversation_segment.customer_text:

        conversation_segment.specialist_text = conversation_segment.customer_text
        # TODO feed to LLM
        kokoro_tts_service.generate_audio_file_from_text(conversation_segment.specialist_text)
        # conversation_segment.callback(text)