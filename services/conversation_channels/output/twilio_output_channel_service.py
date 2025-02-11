import logging
import os

from clients.twilio_rest_client import publish_audio_to_call
from schemas.conversation_segment import ConversationSegment
from utilities.logging_utils import configure_logger


class TwilioOutputChannelService:
    def __init__(self):
        self.logger = configure_logger('twilio_output_channel_service_logger', logging.INFO)
        self.logger.info("Twilio output channel service initializing...")
        self.logger.info("Twilio output channel service initialized")


    def publish_audio(self, conversation_segment: ConversationSegment):
        """Publish audio to Twilio."""
        publish_audio_to_call(conversation_segment.call_id, "https://" + os.getenv('NGROK_DOMAIN') + "/twilio-play?filename=" + conversation_segment.specialist_audio_file)
