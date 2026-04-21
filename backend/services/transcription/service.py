"""Orchestrator for the transcription service.

Supports two modes selected via the TRANSCRIPTION_ENDPOINT_NAME env var:

  • SageMaker mode  — set TRANSCRIPTION_ENDPOINT_NAME; audio is chunked on the
                      backend then each chunk is sent to the GPU endpoint.
  • Local mode      — model is loaded into memory (original behaviour);
                      used when TRANSCRIPTION_ENDPOINT_NAME is not set.
"""

import io
import logging
import os
import traceback

import numpy as np
import soundfile as sf
import torch

from . import audio, config, model
from .exceptions import ModelNotLoadedError
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
            print("transcribing in sagemaker")
            logger.info(
                "TranscriptionService using SageMaker endpoint: %s (%s)",
                endpoint_name,
                region,
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
            self._mode,
            audio_path,
            language,
            minutes_remaining,
        )

        if self._mode == "sagemaker":
            return self._transcribe_sagemaker(audio_path, language, minutes_remaining)
        return self._transcribe_local(audio_path, language, minutes_remaining)

    # SageMaker mode 
    def _transcribe_sagemaker(
        self,
        audio_path: str,
        language: str | None,
        minutes_remaining: float,
    ) -> tuple[str, float]:
        """
        Chunk the audio on the backend, send each chunk to the SageMaker
        GPU endpoint, and join the results.
        """
        # 1. Load & validate audio (reuses existing audio.py utilities)
        audio_data, duration = audio.load_and_validate(audio_path, minutes_remaining)

        # 2. Chunk into ≤30 s segments
        chunks = audio.chunk_audio(audio_data)
        logger.info("Split audio into %d chunk(s) for SageMaker.", len(chunks))

        full_transcription: list[str] = []

        for i, chunk in enumerate(chunks):
            if len(chunk) < 16_000 * 0.1:  # skip chunks shorter than 0.1 s
                continue

            chunk_text = self._sm_client.invoke_chunk(chunk)
            if chunk_text:
                full_transcription.append(chunk_text)
                logger.debug("Chunk %d transcription: %s", i + 1, chunk_text)
            else:
                logger.debug("Chunk %d yielded empty transcription.", i + 1)

        final_text = " ".join(full_transcription).strip()

        if not final_text:
            logger.warning("SageMaker inference yielded no speech across all chunks.")
            return "[No speech detected]", duration

        logger.info("SageMaker transcription complete.")
        return final_text, duration

    # Local mode 
    def _init_local(self, model_path: str) -> None:
        """Load the Whisper model into local memory."""
        full_path, fallback_path = config.resolve_model_paths(model_path)
        self.device, self.torch_dtype = config.detect_device()
        self.processor = model.load_processor(full_path, fallback_path)
        self.model = model.load_model(full_path, self.device, self.torch_dtype)

    def _transcribe_local(
        self,
        audio_path: str,
        language: str | None,
        minutes_remaining: float,
    ) -> tuple[str, float]:
        """Original local inference loop — unchanged from the previous implementation."""
        from .exceptions import TranscriptionError

        try:
            # 1. Load Audio
            audio_data, duration = audio.load_and_validate(audio_path, minutes_remaining)

            # 2. Segment Audio
            chunks = audio.chunk_audio(audio_data)
            logger.info("Split audio into %d chunks for local processing.", len(chunks))

            # 3. Prepare Generation Args
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

            full_transcription: list[str] = []

            # 4. Process Each Chunk
            for i, chunk in enumerate(chunks):
                if len(chunk) < 16_000 * 0.1:
                    continue

                inputs = self.processor(chunk, sampling_rate=16000, return_tensors="pt")
                input_features = inputs.input_features.to(
                    device=self.device, dtype=self.torch_dtype
                )

                with torch.no_grad():
                    predicted_ids = self.model.generate(input_features, **gen_kwargs)

                chunk_text = self.processor.batch_decode(
                    predicted_ids, skip_special_tokens=True
                )[0].strip()

                if chunk_text:
                    full_transcription.append(chunk_text)
                    logger.debug("Chunk %d: %s", i + 1, chunk_text)
                else:
                    logger.debug("Chunk %d yielded empty string.", i + 1)

            final_text = " ".join(full_transcription).strip()

            if not final_text:
                logger.warning("Local inference yielded no speech.")
                return "[No speech detected]", duration

            logger.info("Local transcription completed successfully.")
            return final_text, duration

        except Exception as e:
            logger.error("Local inference error: %s", e)
            traceback.print_exc()
            if isinstance(e, TranscriptionError):
                raise
            return f"[Transcription error: {str(e)}]", 0.0
