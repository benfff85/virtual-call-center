import logging
from typing import Optional

from schemas.conversation_segment import ConversationSegment
from services.agentic_service import AgenticService
from services.audio_persistence_service import AudioPersistenceService
from services.conversation_channels.output.console_output_channel_service import ConsoleOutputChannelService
from services.conversation_channels.output.twilio_output_channel_service import TwilioOutputChannelService
from services.kokoro_tts_service import KokoroTtsService
from services.transcription.transcription_gateway import TranscriptionGateway
from utilities.logging_utils import configure_logger


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
            audio_persistence_service: Optional[AudioPersistenceService] = AudioPersistenceService(),
            logger: Optional[logging.Logger] = configure_logger('conversation_segment_processor_service_logger', logging.INFO)
    ):

        self.transcription_gateway = transcription_gateway or TranscriptionGateway()
        self.agentic_service = agentic_service or AgenticService()
        self.tts_service = tts_service or KokoroTtsService()
        self.audio_persistence_service = audio_persistence_service or AudioPersistenceService()
        self.audio_output_channel = TwilioOutputChannelService() # TODO Consider adding gateway to drive off of convo segment output channel type
        self.console_output_channel = ConsoleOutputChannelService()
        self.logger = logger

    async def process_conversation_segment(self, conversation_segment: ConversationSegment):

        # TODO convert audio format if needed

        # Transcribe audio
        conversation_segment.customer_text = self.transcription_gateway.transcribe(conversation_segment.customer_audio.raw_audio)

        # Guard clause: exit if no transcript was produced
        if not conversation_segment.customer_text:
            return

        # TODO issue interrupt

        # Call AutoGen to generate specialist response text
        conversation_segment.specialist_text = await self.agentic_service.process_async(conversation_segment.customer_text)

        # If just publishing to console do so now and return without generating output audio
        if conversation_segment.output_audio_channel.CONSOLE:
            self.console_output_channel.publish_audio(conversation_segment)
            return

        # Call Kokoro for text to speech
        conversation_segment.specialist_audio_data = self.tts_service.generate_audio_data_from_text(conversation_segment.specialist_text)

        # Save audio to disk
        self.audio_persistence_service.write_wav_file(conversation_segment)

        # Publish audio to Twilio
        self.audio_output_channel.publish_audio(conversation_segment)
