from schemas.conversation_segment import ConversationSegment
from services.agentic_service import AgenticService
from services.kokoro_tts_service import KokoroTtsService
from services.transcription.transcription_gateway import TranscriptionGateway
from utilities.logging_utils import configure_logger
import logging


logger = configure_logger('conversation_segment_processor_service_logger', logging.INFO)

transcription_gateway = TranscriptionGateway()
agentic_service = AgenticService()
tts_service = KokoroTtsService()

async def process_conversation_segment(conversation_segment: ConversationSegment):

    # TODO convert audio format if needed

    # Transcribe audio
    conversation_segment.customer_text = transcription_gateway.transcribe(conversation_segment.customer_audio.raw_audio)

    # Guard clause: exit if no transcript was produced
    if not conversation_segment.customer_text:
        return

    # Call AutoGen to generate specialist response text
    conversation_segment.specialist_text = await agentic_service.process_async(conversation_segment.customer_text)

    # Call Kokoro for text to speech
    wav_file_name = tts_service.generate_audio_file_from_text(conversation_segment.specialist_text)

    # TODO add support for callid and sequence to filename

    conversation_segment.specialist_audio_file = wav_file_name

    # TODO move to audio output channel


if __name__ == '__main__':
    process_conversation_segment()