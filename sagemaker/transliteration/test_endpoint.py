"""
test_endpoint.py — Quick smoke test for the live transliteration SageMaker endpoint.

Run after start_endpoint.py has finished:
    python sagemaker/transliteration/test_endpoint.py

Sends a sample Nepali text string and prints the transliterated result.
"""

import json
import os
import sys
import time
import boto3

ENDPOINT_NAME = os.getenv("TRANSLITERATION_ENDPOINT_NAME", "voicescribe-transliteration-endpoint")
REGION        = os.getenv("AWS_REGION", "ap-south-1")

# Default test text — Nepali script
DEFAULT_TEXT = "नमस्ते संसार"


def test(text: str = DEFAULT_TEXT):
    print(f"Endpoint  : {ENDPOINT_NAME}")
    print(f"Region    : {REGION}")
    print(f"Text      : {text}")
    print()

    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    payload = json.dumps({"text": text})

    print(f"Sending {len(payload)} bytes to endpoint ...")
    start = time.time()

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=payload,
    )

    elapsed = time.time() - start
    result = json.loads(response["Body"].read())

    # Handle list wrapper from DLC serialization
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str):
        result = json.loads(result[0])

    print(f"\n✅ Response in {elapsed:.1f}s")
    print(f"Transliterated : {result.get('transliterated_text', '[empty]')}")


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TEXT
    test(text)
