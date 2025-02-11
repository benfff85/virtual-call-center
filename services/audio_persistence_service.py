import logging
import os

import soundfile as sf

from schemas.conversation_segment import ConversationSegment
from utilities.logging_utils import configure_logger


class AudioPersistenceService:
    def __init__(self):
        self.logger = configure_logger('audio_persistence_service_logger', logging.INFO)
        self.logger.info("Audio persistence service initializing...")
        self.call_id_counters = {}
        self.audio_storage_directory = os.getenv('AUDIO_CLIP_DIR')
        self.logger.info("Audio persistence service initialized")


    def write_wav_file(self, conversation_segment: ConversationSegment):

        call_id = conversation_segment.call_id
        if call_id not in self.call_id_counters:
            self.call_id_counters[call_id] = 0
        else:
            self.call_id_counters[call_id] += 1

        file_name = f"{call_id}-{self.call_id_counters[call_id]}-specialist.wav"

        sf.write(f"{self.audio_storage_directory}/{file_name}", conversation_segment.specialist_audio_data, 24000, format='WAV', subtype='PCM_16')

        conversation_segment.specialist_audio_file = file_name

        self.logger.info(f"Audio file written to disk: {conversation_segment.specialist_audio_file}")
