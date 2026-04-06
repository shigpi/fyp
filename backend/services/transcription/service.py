"""Orchestrator for the transcription service."""

import logging
import traceback

import torch

from . import audio, config, model
from .exceptions import ModelNotLoadedError

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, model_path: str = "ai_models/whisper-nepali-small"):
        """Initialize the Whisper model and processor."""
        try:
            self._init_service(model_path)
            logger.info("TranscriptionService initialized successfully")
        except Exception as e:
            logger.critical("Failed to instantiate TranscriptionService: %s", e)
            traceback.print_exc()
            raise ModelNotLoadedError(str(e)) from e

    def _init_service(self, model_path: str) -> None:
        full_path, fallback_path = config.resolve_model_paths(model_path)
        self.device, self.torch_dtype = config.detect_device()

        self.processor = model.load_processor(full_path, fallback_path)
        self.model = model.load_model(full_path, self.device, self.torch_dtype)

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        minutes_remaining: float = 0,
    ) -> str:
        """
        Transcribe an audio file to text using manual inference loop.

        Args:
            audio_path: Path to the audio file.
            language: Optional hint for transcription language.
            minutes_remaining: Remaining quota limit (0 for unlimited).

        Returns:
            The transcribed text.
        """
        logger.info(
            "Transcribing audio file: %s (Language: %s, Quota: %.1f mins)",
            audio_path,
            language,
            minutes_remaining,
        )

        try:
            # 1. Load Audio
            audio_data, duration = audio.load_and_validate(
                audio_path, minutes_remaining
            )

            # 2. Feature Extraction
            inputs = self.processor(
                audio_data, sampling_rate=16000, return_tensors="pt"
            )

            # 3. Move to Device
            input_features = inputs.input_features.to(
                device=self.device, dtype=self.torch_dtype
            )

            # 4. Prepare Generation Args
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

            logger.debug("Generating with args: %s", gen_kwargs)

            # 5. Generate and Decode
            with torch.no_grad():
                predicted_ids = self.model.generate(input_features, **gen_kwargs)

            text = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[
                0
            ].strip()

            if not text:
                logger.warning("Generation yielded empty string — no speech detected.")
                return "[No speech detected]"

            logger.info("Transcription completed successfully.")
            return text

        except Exception as e:
            logger.error("Inference error: %s", e)
            traceback.print_exc()
            # If it's one of our typed exceptions, let it bubble up
            from .exceptions import TranscriptionError
            if isinstance(e, TranscriptionError):
                raise e
            return f"[Transcription error: {str(e)}]"
