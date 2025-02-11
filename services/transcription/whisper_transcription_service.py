from services.transcription.transcription_service import TranscriptionService
from utilities.logging_utils import configure_logger
import base64
import audioop
import logging
import numpy as np
from pywhispercpp.model import Model
from collections import deque
from typing import Optional
import time

class WhisperTranscriptionService(TranscriptionService):
    def __init__(self, model_name: str,
                 models_dir: str = './models/whisper',
                 silence_duration: float = 1.0,  # Duration of silence to trigger processing (in seconds)
                 sample_rate: int = 16000,
                 max_buffer_duration: float = 30.0):  # Maximum buffer size in seconds
        self.logger = configure_logger('whisper_transcription_service_logger', logging.INFO)
        self.whisper_model = Model(model=model_name, models_dir=models_dir)
        self.sample_rate = sample_rate
        self.silence_duration = silence_duration
        self.max_buffer_size = int(max_buffer_duration * sample_rate)
        self.audio_buffer = deque(maxlen=self.max_buffer_size)
        self.silence_threshold = 0.01
        self.last_transcription = ""
        self.silence_start = None

        # Silence check parameters
        self.samples_since_last_check = 0
        self.samples_per_silence_check = int(0.1 * sample_rate)  # Check silence every 100ms

    def _convert_audio(self, input_audio_data: str) -> np.ndarray:
        """Convert incoming audio data to the format required by Whisper."""
        # Decode base64 and convert from u-law to linear PCM
        audio = base64.b64decode(input_audio_data)
        pcm = audioop.ulaw2lin(audio, 2)  # 8kHz u-law → 16-bit linear

        # Resample from 8kHz to 16kHz
        pcm = audioop.ratecv(
            pcm,
            2,          # Sample width (2 bytes)
            1,          # Channels
            8000,       # Input rate
            16000,      # Output rate
            None
        )[0]

        # Convert to float32 array
        return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

    def _is_silence(self, audio_chunk: np.ndarray) -> bool:
        """Check if an audio chunk is silence based on RMS energy."""
        return np.sqrt(np.mean(audio_chunk**2)) < self.silence_threshold

    def _should_process_buffer(self, audio_chunk: np.ndarray) -> bool:
        """Determine if we should process the buffer based on silence detection."""
        is_current_silence = self._is_silence(audio_chunk)
        current_time = time.time()

        # If we detect sound, reset silence timer
        if not is_current_silence:
            self.silence_start = None
            return False

        # If this is the start of silence, mark the time
        if self.silence_start is None:
            self.silence_start = current_time
            return False

        # If we've had enough silence, process the buffer
        if current_time - self.silence_start >= self.silence_duration:
            return True

        return False

    def _extract_text(self, segments: list) -> Optional[str]:
        """Extract and combine text from all segments, filtering out blank audio."""
        valid_segments = []
        for segment in segments:
            # Get the text field from the segment
            text = getattr(segment, 'text', None)
            if text and text.strip() and text.strip() != '[BLANK_AUDIO]':
                valid_segments.append(text.strip())

        if valid_segments:
            return ' '.join(valid_segments)
        return None

    def process_audio(self, input_audio_data: str) -> Optional[str]:
        """Process incoming audio chunks and return transcription when appropriate."""
        # Convert audio to proper format
        audio_chunk = self._convert_audio(input_audio_data)

        # Add new audio to buffer
        self.audio_buffer.extend(audio_chunk)

        # Accumulate samples since last silence check
        self.samples_since_last_check += len(audio_chunk)

        # Check for silence when we've accumulated enough samples
        if self.samples_since_last_check >= self.samples_per_silence_check:
            # Get the last segment of audio for silence detection
            recent_audio = np.array(list(self.audio_buffer))[-self.samples_per_silence_check:]
            should_process = self._should_process_buffer(recent_audio)

            # Reset the sample counter
            self.samples_since_last_check = 0

            if should_process and len(self.audio_buffer) > 0:
                try:
                    # Convert buffer to numpy array
                    audio_array = np.array(list(self.audio_buffer))

                    # Only process if we have meaningful audio before the silence
                    if not self._is_silence(audio_array[:int(len(audio_array) * 0.8)]):
                        # Log buffer size for debugging
                        self.logger.info(f"Processing transcription for buffer of size: {len(audio_array)} samples")

                        # Transcribe the audio
                        result = self.whisper_model.transcribe(audio_array)
                        text = self._extract_text(result)

                        # Clear the buffer and reset silence detection
                        self.audio_buffer.clear()
                        self.silence_start = None

                        # If we got a result different from the last transcription
                        if text and text != self.last_transcription:
                            self.last_transcription = text
                            self.logger.info("Transcribed: %s", text)
                            return text
                    else:
                        # If the buffer was mostly silence, just clear it
                        self.audio_buffer.clear()
                        self.silence_start = None

                except Exception as e:
                    self.logger.error(f"Transcription error: {str(e)}")
                    self.silence_start = None

        return None