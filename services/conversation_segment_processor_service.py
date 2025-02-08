from schemas.conversation_segment import ConversationSegment
from services.whisper_transcription_service import WhisperTranscriptionService
from utilities.logging_utils import configure_logger
import logging

logger = configure_logger('conversation_segment_processor_service_logger', logging.INFO)

transcription_service = WhisperTranscriptionService(silence_duration=1.0)

def process_conversation_segment(conversation_segment: ConversationSegment):

    # TODO convert audio format if needed

    text = transcription_service.process_audio(conversation_segment.customer_audio.raw_audio)
    if text:

        # TODO feed to LLM

        conversation_segment.callback(text)