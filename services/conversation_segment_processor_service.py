from schemas.conversation_segment import ConversationSegment
from services import kokoro_tts_service
from services.transcription.transcription_gateway import TranscriptionGateway
from utilities.logging_utils import configure_logger
import logging

logger = configure_logger('conversation_segment_processor_service_logger', logging.INFO)

transcription_gateway = TranscriptionGateway()

def process_conversation_segment(conversation_segment: ConversationSegment):

    # TODO convert audio format if needed

    # Transcribe audio
    conversation_segment.customer_text = transcription_gateway.transcribe(conversation_segment.customer_audio.raw_audio)

    # Guard clause: exit if no transcript was produced
    if not conversation_segment.customer_text:
        return

    conversation_segment.specialist_text = conversation_segment.customer_text
    # TODO feed to LLM
    kokoro_tts_service.generate_audio_file_from_text(conversation_segment.specialist_text)
    # conversation_segment.callback(text)