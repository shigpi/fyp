"""Boto3 client for invoking the VoiceScribe SageMaker transliteration endpoint."""

import json
import logging
import os
import time

logger = logging.getLogger(__name__)


class SageMakerTransliterationClient:
    """
    Sends text to a SageMaker real-time endpoint and returns transliterations.

    The FastAPI backend uses this client when TRANSLITERATION_ENDPOINT_NAME is set.
    Each call to `transliterate()` sends a text string and receives the
    transliterated output.
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
            "SageMakerTransliterationClient initialised — endpoint: %s, region: %s",
            endpoint_name,
            region,
        )

    def transliterate(self, text: str) -> str:
        """
        Send text to the SageMaker endpoint and return transliterated text.

        Args:
            text: Input text (Nepali / code-mixed) to transliterate.

        Returns:
            Transliterated text string.

        Raises:
            RuntimeError: If the endpoint invocation fails after retries.
        """
        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = self._client.invoke_endpoint(
                    EndpointName=self.endpoint_name,
                    ContentType="application/json",
                    Body=json.dumps({"text": text}),
                )
                result = json.loads(response["Body"].read())

                # Handle list wrapper if present (DLC serialization quirk)
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str):
                    result = json.loads(result[0])

                return result.get("transliterated_text", text)

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
                    logger.error("SageMaker transliteration error: %s", e)
                    raise RuntimeError(f"SageMaker transliteration failed: {e}") from e

        raise RuntimeError(
            f"SageMaker endpoint not ready after {self.max_retries + 1} attempts: {last_error}"
        )
