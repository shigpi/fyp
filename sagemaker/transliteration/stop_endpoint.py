"""
stop_endpoint.py — Delete the Transliteration SageMaker endpoint to stop billing.

Run this after a demo or test session:
    python sagemaker/transliteration/stop_endpoint.py

Billing stops immediately upon deletion.
The endpoint can be re-created any time with start_endpoint.py.
"""

import os
import boto3

ENDPOINT_NAME = os.getenv("TRANSLITERATION_ENDPOINT_NAME", "voicescribe-transliteration-endpoint")
REGION        = os.getenv("AWS_REGION", "ap-south-1")


def stop():
    print(f"Deleting SageMaker endpoint: {ENDPOINT_NAME} (region: {REGION})")
    print("Billing stops immediately.\n")

    sm = boto3.client("sagemaker", region_name=REGION)

    # ── Delete Endpoint ────────────────────────────────────────────────────────
    try:
        sm.delete_endpoint(EndpointName=ENDPOINT_NAME)
        print(f"✅ Endpoint '{ENDPOINT_NAME}' deleted.")
    except sm.exceptions.ClientError as e:
        if "Could not find endpoint" in str(e):
            print(f"⚠️  Endpoint '{ENDPOINT_NAME}' not found — may already be deleted.")
        else:
            raise

    # ── Delete Endpoint Config ─────────────────────────────────────────────────
    try:
        sm.delete_endpoint_config(EndpointConfigName=ENDPOINT_NAME)
        print(f"✅ Endpoint config '{ENDPOINT_NAME}' deleted.")
    except Exception:
        pass  # Config may not exist or may have a different name

    print("\nDone. Comment out TRANSLITERATION_ENDPOINT_NAME in .env to use local model.")
    print("Re-deploy any time with: python sagemaker/transliteration/start_endpoint.py")


if __name__ == "__main__":
    stop()
