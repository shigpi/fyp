"""Orchestrator for the transcription service (Lambda deployment).

In this deployment build, SageMaker handles all audio processing (loading,
chunking, Whisper inference). Lambda only reads the file bytes, performs a
lightweight quota check, and forwards to SageMaker.

Supports two modes selected via the TRANSCRIPTION_ENDPOINT_NAME env var:

  - SageMaker mode  — set TRANSCRIPTION_ENDPOINT_NAME; raw audio bytes are
                      sent to the GPU endpoint for full processing.
  - Local mode      — model is loaded into memory (original behaviour);
                      used when TRANSCRIPTION_ENDPOINT_NAME is not set.
"""

import io
import logging
import os
import traceback
import wave

from .exceptions import ModelNotLoadedError, QuotaExceededError
from .sagemaker_client import SageMakerTranscriptionClient

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, model_path: str = "ai_models/whisper-nepali-small"):
        """
        Initialise in either SageMaker or local mode.

        SageMaker mode is activated when the environment variable
        TRANSCRIPTION_ENDPOINT_NAME is set to a non-empty string.
        """
        endpoint_name = os.getenv("TRANSCRIPTION_ENDPOINT_NAME", "").strip()

        if endpoint_name:
            region = os.getenv("AWS_REGION", "ap-south-1")
            self._sm_client = SageMakerTranscriptionClient(endpoint_name, region)
            self._mode = "sagemaker"
            logger.info(
                "TranscriptionService using SageMaker endpoint: %s (%s)",
                endpoint_name, region,
            )
        else:
            try:
                self._init_local(model_path)
                self._mode = "local"
                logger.info("TranscriptionService initialised in local mode.")
            except Exception as e:
                logger.critical("Failed to instantiate TranscriptionService: %s", e)
                traceback.print_exc()
                raise ModelNotLoadedError(str(e)) from e

    # ── Public API ─────────────────────────────────────────────────────────────

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        minutes_remaining: float = 0,
    ) -> tuple[str, float]:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file.
            language: Optional language hint ("nepali" / "english").
            minutes_remaining: Remaining quota in minutes (0 = unlimited).

        Returns:
            Tuple of (transcribed_text, duration_seconds).
        """
        logger.info(
            "Transcribing [%s mode] — file: %s, language: %s, quota: %.1f min",
            self._mode, audio_path, language, minutes_remaining,
        )

        if self._mode == "sagemaker":
            return self._transcribe_sagemaker(audio_path, language, minutes_remaining)
        return self._transcribe_local(audio_path, language, minutes_remaining)

    # ── SageMaker mode ─────────────────────────────────────────────────────────

    def _transcribe_sagemaker(
        self,
        audio_path: str,
        language: str | None,
        minutes_remaining: float,
    ) -> tuple[str, float]:
        """
        Read raw audio bytes and send the entire file to SageMaker.
        SageMaker handles loading, chunking, and Whisper inference.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Quick duration estimate from WAV header (stdlib — no librosa needed)
        duration = self._get_wav_duration(audio_path)

        # Quota check before sending to SageMaker
        if minutes_remaining > 0 and duration > 0 and duration > minutes_remaining * 60:
            raise QuotaExceededError(duration, minutes_remaining)

        # Read raw file bytes and send to SageMaker
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        logger.info("Sending %d bytes to SageMaker (estimated %.1fs)", len(audio_bytes), duration)
        result = self._sm_client.invoke(audio_bytes)

        text = result.get("transcription", "").strip()
        # Use SageMaker's measured duration (more accurate than WAV header estimate)
        sm_duration = result.get("duration", duration)

        if not text:
            logger.warning("SageMaker returned empty transcription.")
            return "[No speech detected]", sm_duration

        logger.info("SageMaker transcription complete (%.1fs).", sm_duration)
        return text, sm_duration

    @staticmethod
    def _get_wav_duration(audio_path: str) -> float:
        """Get audio duration from WAV header using stdlib. Returns 0 for non-WAV."""
        try:
            with wave.open(audio_path, "rb") as wf:
                return wf.getnframes() / float(wf.getframerate())
        except Exception:
            return 0.0

    # ── Local mode ─────────────────────────────────────────────────────────────

    def _init_local(self, model_path: str) -> None:
        """Load the Whisper model into local memory."""
        from . import config as _config, model as _model

        full_path, fallback_path = _config.resolve_model_paths(model_path)
        self.device, self.torch_dtype = _config.detect_device()
        self.processor = _model.load_processor(full_path, fallback_path)
        self.model = _model.load_model(full_path, self.device, self.torch_dtype)

    def _transcribe_local(
        self,
        audio_path: str,
        language: str | None,
        minutes_remaining: float,
    ) -> tuple[str, float]:
        """Original local inference loop — unchanged from the previous implementation."""
        from . import audio
        from .exceptions import TranscriptionError

        try:
            audio_data, duration = audio.load_and_validate(audio_path, minutes_remaining)
            chunks = audio.chunk_audio(audio_data)
            logger.info("Split audio into %d chunks for local processing.", len(chunks))

            gen_kwargs = {
                "max_new_tokens": 440,
                "return_timestamps": False,
                "num_beams": 1,
                "do_sample": False,
                "repetition_penalty": 1.1,
                "task": "transcribe",
                "forced_decoder_ids": None,
            }

            if language:
                lang_code = language.lower()
                if lang_code in ["ne", "nepali"]:
                    gen_kwargs["language"] = "nepali"
                elif lang_code in ["en", "english"]:
                    gen_kwargs["language"] = "english"
                else:
                    gen_kwargs["language"] = language

            full_transcription: list[str] = []

            for i, chunk in enumerate(chunks):
                if len(chunk) < 16_000 * 0.1:
                    continue

                inputs = self.processor(chunk, sampling_rate=16000, return_tensors="pt")
                input_features = inputs.input_features.to(
                    device=self.device, dtype=self.torch_dtype
                )

                import torch as _torch
                with _torch.no_grad():
                    predicted_ids = self.model.generate(input_features, **gen_kwargs)

                chunk_text = self.processor.batch_decode(
                    predicted_ids, skip_special_tokens=True
                )[0].strip()

                if chunk_text:
                    full_transcription.append(chunk_text)

            final_text = " ".join(full_transcription).strip()
            if not final_text:
                return "[No speech detected]", duration

            return final_text, duration

        except Exception as e:
            logger.error("Local inference error: %s", e)
            traceback.print_exc()
            if isinstance(e, TranscriptionError):
                raise
            return f"[Transcription error: {str(e)}]", 0.0
