import sounddevice as sd
import numpy as np
import base64
import logging
import threading
import time
import audioop
from typing import Optional
from queue import Queue
from utilities.logging_utils import configure_logger

class MicrophoneInputChannelService:
    def __init__(self,
                 transcription_service,
                 sample_rate: int = 8000,
                 chunk_duration: float = 0.128):
        """
        Initialize the microphone input channel service.

        Args:
            transcription_service: Instance of WhisperTranscriptionService
            sample_rate: Audio sample rate (default 8000 Hz)
            chunk_duration: How many seconds of audio to process at once
        """
        self.logger = configure_logger('micro', logging.INFO)

        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.transcription_service = transcription_service

        # Stream control
        self.is_recording = False
        self.stream_initialized = False

        # Processing thread and queue
        self.audio_queue = Queue()
        self.processing_thread = None

        self.logger.info("Microphone input channel initialized")

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for the sounddevice InputStream."""
        if status:
            self.logger.warning(f"Audio status: {status}")

        if self.stream_initialized:
            try:
                # Convert float32 to int16 PCM
                # indata = (indata.flatten() * 32767).astype(np.int16)  # Convert float32 to int16 PCM with clipping
                indata = np.clip(indata, -1.0, 1.0)  # Add this line to prevent overflow
                audio_pcm = (indata.flatten() * 32767).astype(np.int16)

                # Convert to bytes
                audio_bytes = audio_pcm.tobytes()

                # Convert to u-law
                audio_ulaw = audioop.lin2ulaw(audio_bytes, 2)  # 2 bytes per sample

                # Encode to base64
                encoded = base64.b64encode(audio_ulaw).decode('utf-8')

                # Add to processing queue
                self.logger.info(f"Adding audio data to queue encoded length: {len(encoded)}")
                self.audio_queue.put(encoded)

            except Exception as e:
                self.logger.error(f"Error in audio callback: {str(e)}")

    def _process_audio_queue(self):
        """Process audio data from the queue continuously."""
        self.logger.info("Audio processing thread started")

        while self.is_recording:
            try:
                # Get audio data from queue with timeout
                audio_data = self.audio_queue.get(timeout=1.0)
                self.logger.info(f"process_audio_queue: audio_data length: {len(audio_data)}")

                # Send to transcription service
                text = self.transcription_service.process_audio(audio_data)
                if text:
                    self.logger.info(f"Transcribed: {text}")

            except Exception as e:
                if self.is_recording:
                    self.logger.error(f"Error processing audio: {str(e)}")

    def start_recording(self):
        """Start recording from the microphone."""
        if self.is_recording:
            self.logger.warning("Already recording")
            return

        try:
            self.is_recording = True
            self.stream_initialized = True

            # Corrected samplerate and blocksize
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,  # Use configured sample rate (8000)
                channels=1,
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * self.chunk_duration),  # Correct blocksize
                dtype=np.float32
            )
            self.stream.start()

            # Start the processing thread
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
        """Stop recording from the microphone."""
        if not self.is_recording:
            return

        self.is_recording = False
        self.stream_initialized = False

        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)

        self.logger.info("Recording stopped")

    def __del__(self):
        """Cleanup when the object is destroyed."""
        self.stop_recording()