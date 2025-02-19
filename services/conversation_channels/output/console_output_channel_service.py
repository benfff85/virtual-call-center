import logging

from schemas.conversation_segment import ConversationSegment
from utilities.logging_utils import configure_logger


class ConsoleOutputChannelService:
    def __init__(self):
        self.logger = configure_logger('console_output_channel_service_logger', logging.INFO)
        self.logger.info("Console output channel service initializing...")
        self.logger.info("Console output channel service initialized")


    def publish_audio(self, conversation_segment: ConversationSegment):
        """Publish specialist text to console."""
        self.logger.info(
            f"""
===================================== Specialist =====================================
{conversation_segment.specialist_text}
======================================================================================
            """
        )