import logging
import os
from typing import Optional

from clients.twilio_rest_client import interrupt_specialist_audio
from schemas.conversation_output_channel_type import ConversationOutputChannelType
from schemas.conversation_segment import ConversationSegment
from services.audio_persistence_service import AudioPersistenceService
from services.conversation_channels.output.console_output_channel_service import ConsoleOutputChannelService
from services.conversation_channels.output.twilio_output_channel_service import TwilioOutputChannelService
from services.transcription.transcription_gateway import TranscriptionGateway
from services.tts.kokoro_tts_service import KokoroTtsService
from utilities.logging_utils import configure_logger


class ConversationSegmentProcessorService:
    """
    Processes conversation segments by transcribing audio,
    generating specialist responses, and creating audio output.
    """

    def __init__(
            self,
            transcription_gateway: Optional[TranscriptionGateway] = TranscriptionGateway(),
            tts_service: Optional[KokoroTtsService] = KokoroTtsService(),
            audio_persistence_service: Optional[AudioPersistenceService] = AudioPersistenceService(),
            logger: Optional[logging.Logger] = configure_logger('conversation_segment_processor_service_logger', logging.INFO)
    ):

        self.transcription_gateway = transcription_gateway or TranscriptionGateway()
        self.tts_service = tts_service or KokoroTtsService()
        self.audio_persistence_service = audio_persistence_service or AudioPersistenceService()
        self.audio_output_channel = TwilioOutputChannelService() # TODO Consider adding gateway to drive off of convo segment output channel type
        self.console_output_channel = ConsoleOutputChannelService()

        if os.environ.get('AGENT_TYPE') == 'simple':
            from services.agents.agentic_service import AgenticService
        else:
            from services.agents.agentic_service_complex_team import AgenticService
        self.agentic_service = AgenticService()

        self.logger = logger

    async def process_conversation_segment(self, conversation_segment: ConversationSegment):

        # TODO convert audio format if needed

        # Transcribe audio
        conversation_segment.customer_text = self.transcription_gateway.transcribe(conversation_segment.customer_audio.raw_audio)

        # Guard clause: exit if no transcript was produced
        if not conversation_segment.customer_text:
            return

        # If using twilio as audio output interrupt the specialist of they're currently speaking
        if conversation_segment.output_audio_channel == ConversationOutputChannelType.TWILIO:
            interrupt_specialist_audio(conversation_segment.call_id)

        # Call AutoGen to generate specialist response text
        conversation_segment.specialist_text = await self.agentic_service.process_async(conversation_segment.customer_text, conversation_segment.call_id)

        # If just publishing to console do so now and return without generating output audio
        if conversation_segment.output_audio_channel == ConversationOutputChannelType.CONSOLE:
            self.console_output_channel.publish_audio(conversation_segment)
            return

        # Call Kokoro for text to speech
        conversation_segment.specialist_audio_data = self.tts_service.generate_audio_data_from_text(conversation_segment.specialist_text)

        # Save audio to disk
        self.audio_persistence_service.write_wav_file(conversation_segment)

        # Publish audio to Twilio
        self.audio_output_channel.publish_audio(conversation_segment)
