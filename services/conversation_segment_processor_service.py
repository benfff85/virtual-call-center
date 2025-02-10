from typing import Optional

from schemas.conversation_segment import ConversationSegment
from services.agentic_service import AgenticService
from services.kokoro_tts_service import KokoroTtsService
from services.transcription.transcription_gateway import TranscriptionGateway
from utilities.logging_utils import configure_logger
import logging


class ConversationSegmentProcessorService:
    """
    Processes conversation segments by transcribing audio,
    generating specialist responses, and creating audio output.
    """

    def __init__(
            self,
            transcription_gateway: Optional[TranscriptionGateway] = TranscriptionGateway(),
            agentic_service: Optional[AgenticService] = AgenticService(),
            tts_service: Optional[KokoroTtsService] = KokoroTtsService(),
            logger: Optional[logging.Logger] = configure_logger('conversation_segment_processor_service_logger', logging.INFO)
    ):

        self.transcription_gateway = transcription_gateway or TranscriptionGateway()
        self.agentic_service = agentic_service or AgenticService()
        self.tts_service = tts_service or KokoroTtsService()
        self.logger = logger

    async def process_conversation_segment(self, conversation_segment: ConversationSegment):

        # TODO convert audio format if needed

        # Transcribe audio
        conversation_segment.customer_text = self.transcription_gateway.transcribe(conversation_segment.customer_audio.raw_audio)

        # Guard clause: exit if no transcript was produced
        if not conversation_segment.customer_text:
            return

        # Call AutoGen to generate specialist response text
        conversation_segment.specialist_text = await self.agentic_service.process_async(conversation_segment.customer_text)

        # Call Kokoro for text to speech
        wav_file_name = self.tts_service.generate_audio_file_from_text(conversation_segment.specialist_text)

        # TODO add support for callid and sequence to filename

        conversation_segment.specialist_audio_file = wav_file_name

        # TODO move to audio output channel
