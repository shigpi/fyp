"""Boto3 client for invoking the VoiceScribe SageMaker Whisper endpoint."""

import io
import json
import logging
import os
import time

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

# Maximum payload size SageMaker real-time endpoints accept (6 MB)
_MAX_PAYLOAD_BYTES = 6 * 1024 * 1024


class SageMakerTranscriptionClient:
    """
    Sends audio chunks to a SageMaker real-time endpoint and returns transcriptions.

    The FastAPI backend uses this client when SAGEMAKER_ENDPOINT_NAME is set.
    Each call to `invoke_chunk()` sends one ≤30 s audio numpy array as WAV bytes.
    """

    def __init__(
        self,
        endpoint_name: str,
        region: str = "ap-south-1",
        max_retries: int = 2,
        retry_delay: float = 5.0,
    ):
        import boto3

        self.endpoint_name = endpoint_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = boto3.client("sagemaker-runtime", region_name=region)
        logger.info(
            "SageMakerTranscriptionClient initialised — endpoint: %s, region: %s",
            endpoint_name,
            region,
        )

    def invoke_chunk(self, audio_chunk: np.ndarray, sample_rate: int = 16_000) -> str:
        """
        Send a single audio chunk (≤30 s, 16 kHz float32) to the SageMaker endpoint.

        Args:
            audio_chunk: Numpy float32 array of audio samples at `sample_rate`.
            sample_rate: Sampling rate of the audio (default 16 kHz).

        Returns:
            Transcription string for this chunk.

        Raises:
            RuntimeError: If the endpoint invocation fails after retries.
        """
        wav_bytes = self._array_to_wav_bytes(audio_chunk, sample_rate)

        if len(wav_bytes) > _MAX_PAYLOAD_BYTES:
            logger.warning(
                "Chunk payload %d bytes exceeds 6 MB limit — trimming chunk.",
                len(wav_bytes),
            )
            # Trim chunk to fit — very unlikely with ≤30 s at 16 kHz
            max_samples = (_MAX_PAYLOAD_BYTES // 4) - 1000
            audio_chunk = audio_chunk[:max_samples]
            wav_bytes = self._array_to_wav_bytes(audio_chunk, sample_rate)

        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = self._client.invoke_endpoint(
                    EndpointName=self.endpoint_name,
                    ContentType="audio/wav",
                    Body=wav_bytes,
                )
                result = json.loads(response["Body"].read())
                
                # Handle tuple returned by output_fn being serialized as list by DLC
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str):
                    result = json.loads(result[0])
                
                return result.get("transcription", "")

            except Exception as e:
                last_error = e
                err_str = str(e)
                if "ModelNotReadyException" in err_str or "ModelError" in err_str:
                    logger.warning(
                        "Endpoint not ready (attempt %d/%d) — retrying in %.0fs ...",
                        attempt,
                        self.max_retries + 1,
                        self.retry_delay,
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error("SageMaker invocation error: %s", e)
                    raise RuntimeError(f"SageMaker invocation failed: {e}") from e

        raise RuntimeError(
            f"SageMaker endpoint not ready after {self.max_retries + 1} attempts: {last_error}"
        )

    @staticmethod
    def _array_to_wav_bytes(audio: np.ndarray, sr: int) -> bytes:
        """Encode a float32 numpy array to WAV bytes in memory."""
        buf = io.BytesIO()
        sf.write(buf, audio.astype(np.float32), sr, format="WAV", subtype="FLOAT")
        buf.seek(0)
        return buf.read()
