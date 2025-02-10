from schemas.conversation_segment import ConversationSegment
from services import kokoro_tts_service
from services.agentic_service import AgenticService
from services.transcription.transcription_gateway import TranscriptionGateway
from utilities.logging_utils import configure_logger
import logging


logger = configure_logger('conversation_segment_processor_service_logger', logging.INFO)

transcription_gateway = TranscriptionGateway()
agentic_service = AgenticService()

def process_conversation_segment(conversation_segment: ConversationSegment):

    # TODO convert audio format if needed

    # Transcribe audio
    conversation_segment.customer_text = transcription_gateway.transcribe(conversation_segment.customer_audio.raw_audio)

    # Guard clause: exit if no transcript was produced
    if not conversation_segment.customer_text:
        return

    # conversation_segment.specialist_text = conversation_segment.customer_text
    conversation_segment.specialist_text = agentic_service.process(conversation_segment.customer_text)

    wav_file_name = kokoro_tts_service.generate_audio_file_from_text(conversation_segment.specialist_text)
    # conversation_segment.callback(text)

    # TODO move to audio output channel


if __name__ == '__main__':
    process_conversation_segment()