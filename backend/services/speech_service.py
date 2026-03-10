try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: faster-whisper not available. Speech-to-text will be disabled.")

from config import settings
import os
import tempfile

class SpeechToTextService:
    def __init__(self):
        self.model = None
        self.model_size = settings.WHISPER_MODEL
        self.available = WHISPER_AVAILABLE

    def load_model(self):
        """Lazy load the Whisper model"""
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper is not available. Please type your answers instead.")

        if self.model is None:
            print(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )
            print("Whisper model loaded successfully")

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file to text"""
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Speech-to-text is not available. Please type your answer instead.")

        self.load_model()

        segments, info = self.model.transcribe(
            audio_file_path,
            language="en",
            beam_size=5
        )

        transcription = " ".join([segment.text for segment in segments])
        return transcription.strip()

    async def transcribe_audio_bytes(self, audio_bytes: bytes) -> str:
        """Transcribe audio from bytes"""
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Speech-to-text is not available. Please type your answer instead.")

        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            transcription = await self.transcribe_audio(tmp_path)
            return transcription
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

speech_to_text_service = SpeechToTextService()
