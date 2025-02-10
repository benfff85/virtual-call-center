import uuid

import sounddevice as sd
import numpy as np
import base64
import logging
import threading
import audioop
from queue import Queue
from schemas.audio_data import AudioData
from schemas.conversation_input_channel_type import ConversationInputChannelType

from schemas.conversation_segment import ConversationSegment
from services.conversation_segment_processor_service import ConversationSegmentProcessorService
from utilities.logging_utils import configure_logger

class MicrophoneInputChannelService:
    def __init__(self,
                 sample_rate: int = 8000,
                 chunk_duration: float = 0.128):
        """
        Initialize the microphone input channel service.
        """
        self.logger = configure_logger('microphone_input_channel_service_logger', logging.INFO)
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)

        # Stream control
        self.is_recording = False
        self.stream_initialized = False

        # Processing thread and queue
        self.audio_queue = Queue()
        self.processing_thread = None

        self.call_id = str(uuid.uuid4())
        self.conversation_segment_processor_service = ConversationSegmentProcessorService()


        self.logger.info("Microphone input channel initialized")

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for the sounddevice InputStream."""
        if status:
            self.logger.warning(f"Audio status: {status}")

        if self.stream_initialized:
            try:
                # Prevent overflow and convert to int16 PCM
                indata = np.clip(indata, -1.0, 1.0)
                audio_pcm = (indata.flatten() * 32767).astype(np.int16)
                audio_bytes = audio_pcm.tobytes()

                # Convert to u-law (2 bytes per sample)
                audio_ulaw = audioop.lin2ulaw(audio_bytes, 2)

                # Encode to base64
                encoded = base64.b64encode(audio_ulaw).decode('utf-8')

                self.audio_queue.put(encoded)
            except Exception as e:
                self.logger.error(f"Error in audio callback: {str(e)}")

    def _process_audio_queue(self):
        """Continuously process audio data from the queue."""
        self.logger.info("Audio processing thread started")
        while self.is_recording:
            try:
                audio_data = self.audio_queue.get(timeout=1.0)

                # Instantiate a ConversationSegment object
                conversation_segment = ConversationSegment(
                    call_id=self.call_id,
                    input_audio_channel=ConversationInputChannelType.LAPTOP_MICROPHONE,
                    customer_audio=AudioData(raw_audio=audio_data, format="ULAW", frequency=8000, channels=1, bit_depth=16),
                    callback=lambda specialist_text: self.logger.info(f"Transcribed customer audio: {specialist_text}")
                )

                self.conversation_segment_processor_service.process_conversation_segment(conversation_segment)

            except Exception as e:
                if self.is_recording:
                    self.logger.error(f"Error processing audio: {str(e)}")

    def start_recording(self):
        """Start recording audio from the microphone."""
        if self.is_recording:
            self.logger.warning("Already recording")
            return

        try:
            self.is_recording = True
            self.stream_initialized = True

            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * self.chunk_duration),
                dtype=np.float32
            )
            self.stream.start()

            # Start a separate thread to process audio data from the queue
            self.processing_thread = threading.Thread(
                target=self._process_audio_queue,
                daemon=True
            )
            self.processing_thread.start()

            self.logger.info("Recording started")
        except Exception as e:
            self.is_recording = False
            self.stream_initialized = False
            self.logger.error(f"Error starting recording: {str(e)}")
            raise

    def stop_recording(self):
        """Stop recording audio from the microphone."""
        if not self.is_recording:
            return

        self.is_recording = False
        self.stream_initialized = False

        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)

        self.logger.info("Recording stopped")

    def __del__(self):
        """Cleanup resources on object deletion."""
        self.stop_recording()


def run_microphone_mode():
    """Runs the microphone input channel service in standalone mode."""
    import time
    logger = configure_logger('microphone_main', logging.INFO)
    logger.info("Starting microphone input channel service in standalone mode.")
    recorder = MicrophoneInputChannelService()
    recorder.start_recording()
    try:
        logger.info("Recording from microphone... Press Ctrl+C to stop.")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Stopping microphone recording...")
    finally:
        recorder.stop_recording()
        logger.info("Microphone recording stopped.")
