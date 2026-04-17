"""
test_endpoint.py — Quick smoke test for the live SageMaker endpoint.

Run after start_endpoint.py has finished:
    python sagemaker/test_endpoint.py

Uses dummy.wav from the project root. Prints the transcription result.
"""

import json
import os
import sys
import time
import boto3

ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "voicescribe-whisper-endpoint")
REGION        = os.getenv("AWS_REGION", "ap-south-1")

# default test file — dummy.wav in project root
DEFAULT_AUDIO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dummy.wav")


def test(audio_path: str = DEFAULT_AUDIO):
    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        sys.exit(1)

    print(f"Endpoint  : {ENDPOINT_NAME}")
    print(f"Region    : {REGION}")
    print(f"Audio     : {audio_path}")
    print()

    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    print(f"Sending {len(audio_bytes) / 1024:.1f} KB to endpoint ...")
    start = time.time()

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="audio/wav",
        Body=audio_bytes,
    )

    elapsed = time.time() - start
    result = json.loads(response["Body"].read())

    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str):
        result = json.loads(result[0])

    print(f"\n✅ Response in {elapsed:.1f}s")
    print(f"Transcription : {result.get('transcription', '[empty]')}")
    print(f"Duration      : {result.get('duration', '?'):.2f}s")


if __name__ == "__main__":
    audio = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_AUDIO
    test(audio)
