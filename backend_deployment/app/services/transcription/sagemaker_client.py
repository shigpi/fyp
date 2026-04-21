"""Boto3 client for invoking the VoiceScribe SageMaker Whisper endpoint.

Sends raw audio file bytes to SageMaker (which handles loading, chunking,
and inference). Returns transcription text and duration.
"""

import json
import logging
import time

logger = logging.getLogger(__name__)

# Maximum payload size SageMaker real-time endpoints accept (6 MB)
_MAX_PAYLOAD_BYTES = 6 * 1024 * 1024


class SageMakerTranscriptionClient:
    """
    Sends raw audio bytes to a SageMaker real-time endpoint.

    The FastAPI backend uses this client when TRANSCRIPTION_ENDPOINT_NAME is set.
    SageMaker handles audio loading, chunking, and Whisper inference.
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
            endpoint_name, region,
        )

    def invoke(self, audio_bytes: bytes) -> dict:
        """
        Send raw audio file bytes to the SageMaker endpoint.

        Args:
            audio_bytes: Raw bytes of the audio file (WAV, MP3, etc).

        Returns:
            dict with "transcription" (str) and "duration" (float seconds).

        Raises:
            RuntimeError: If the endpoint invocation fails after retries.
        """
        if len(audio_bytes) > _MAX_PAYLOAD_BYTES:
            logger.warning(
                "Audio payload %d bytes exceeds 6 MB limit — SageMaker may reject it.",
                len(audio_bytes),
            )

        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = self._client.invoke_endpoint(
                    EndpointName=self.endpoint_name,
                    ContentType="audio/wav",
                    Body=audio_bytes,
                )
                result = json.loads(response["Body"].read())

                # Handle tuple returned by output_fn being serialized as list by DLC
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str):
                    result = json.loads(result[0])

                return {
                    "transcription": result.get("transcription", ""),
                    "duration": result.get("duration", 0.0),
                }

            except Exception as e:
                last_error = e
                err_str = str(e)
                if "ModelNotReadyException" in err_str or "ModelError" in err_str:
                    logger.warning(
                        "Endpoint not ready (attempt %d/%d) — retrying in %.0fs ...",
                        attempt, self.max_retries + 1, self.retry_delay,
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error("SageMaker invocation error: %s", e)
                    raise RuntimeError(f"SageMaker invocation failed: {e}") from e

        raise RuntimeError(
            f"SageMaker endpoint not ready after {self.max_retries + 1} attempts: {last_error}"
        )
