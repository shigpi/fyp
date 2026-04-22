"""
update_endpoint.py — Update the Whisper SageMaker endpoint with new inference code.

Bundles the updated code/, uploads a new model.tar.gz, creates a new
Model + EndpointConfig, and updates the existing endpoint in-place.

Usage:
    uv run python sagemaker/transcription/update_endpoint.py
"""

import os
import sys
import tarfile
import time

import boto3
import sagemaker
from sagemaker.huggingface.model import HuggingFaceModel

# ── Configuration ──────────────────────────────────────────────────────────────
HF_MODEL_ID   = "kkarhm/whisper-nep-eng-codemixed-small"
ENDPOINT_NAME = "voicescribe-whisper-endpoint"
INSTANCE_TYPE = "ml.g4dn.xlarge"
REGION        = os.getenv("AWS_REGION", "ap-south-1")

TRANSFORMERS_VERSION = "4.37.0"
PYTORCH_VERSION      = "2.1.0"
PY_VERSION           = "py310"

_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CODE_DIR     = os.path.join(_SCRIPT_DIR, "code")
TARBALL_PATH = os.path.join(_SCRIPT_DIR, "model.tar.gz")


def _bundle_code() -> str:
    """Package code/ into model.tar.gz."""
    print(f"Bundling inference code: {CODE_DIR}")
    with tarfile.open(TARBALL_PATH, "w:gz") as tar:
        for fname in os.listdir(CODE_DIR):
            fpath = os.path.join(CODE_DIR, fname)
            tar.add(fpath, arcname=os.path.join("code", fname))
    size_kb = os.path.getsize(TARBALL_PATH) / 1024
    print(f"  → Created {TARBALL_PATH} ({size_kb:.1f} KB)")
    return TARBALL_PATH


def _upload_to_s3(sm_session: sagemaker.Session) -> str:
    """Upload the code tarball to the default SageMaker S3 bucket."""
    s3_uri = sm_session.upload_data(
        path=TARBALL_PATH,
        key_prefix="voicescribe-whisper/code",
    )
    print(f"  → Uploaded to {s3_uri}")
    return s3_uri


def update():
    print("=" * 60)
    print("VoiceScribe — Update SageMaker Whisper Endpoint")
    print("=" * 60)
    print(f"  Region      : {REGION}")
    print(f"  Endpoint    : {ENDPOINT_NAME}")
    print(f"  Instance    : {INSTANCE_TYPE}")
    print()

    boto_session = boto3.Session(region_name=REGION)
    sm_client    = boto_session.client("sagemaker")
    sm_session   = sagemaker.Session(boto_session=boto_session)

    # Check endpoint exists
    try:
        resp = sm_client.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = resp["EndpointStatus"]
        print(f"  Current status: {status}")
    except sm_client.exceptions.ClientError:
        print(f"Endpoint '{ENDPOINT_NAME}' not found. Use start_endpoint.py instead.")
        sys.exit(1)

    # IAM Role
    role = os.getenv("SAGEMAKER_ROLE_ARN", "").strip()
    if not role:
        role = input("Paste your SageMaker IAM Role ARN: ").strip()
        if not role.startswith("arn:aws:iam::"):
            print("Invalid ARN format. Exiting.")
            sys.exit(1)

    print(f"  IAM Role    : {role}")
    print()

    # Bundle & Upload
    _bundle_code()
    model_data = _upload_to_s3(sm_session)
    print()

    # Create new model
    timestamp = int(time.time())
    model_name = f"voicescribe-whisper-{timestamp}"

    model = HuggingFaceModel(
        model_data=model_data,
        role=role,
        sagemaker_session=sm_session,
        transformers_version=TRANSFORMERS_VERSION,
        pytorch_version=PYTORCH_VERSION,
        py_version=PY_VERSION,
        name=model_name,
        env={
            "HF_MODEL_ID": HF_MODEL_ID,
        },
    )

    print(f"Creating new model: {model_name}")
    model.create(instance_type=INSTANCE_TYPE)

    # Create new endpoint config
    config_name = f"voicescribe-whisper-config-{timestamp}"
    print(f"Creating endpoint config: {config_name}")
    sm_client.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[{
            "VariantName": "AllTraffic",
            "ModelName": model_name,
            "InstanceType": INSTANCE_TYPE,
            "InitialInstanceCount": 1,
        }],
    )

    # Update endpoint
    print(f"\nUpdating endpoint '{ENDPOINT_NAME}'...")
    print("This takes ~5-10 minutes (blue/green deployment)...\n")
    start = time.time()

    sm_client.update_endpoint(
        EndpointName=ENDPOINT_NAME,
        EndpointConfigName=config_name,
    )

    # Wait for update
    waiter = sm_client.get_waiter("endpoint_in_service")
    waiter.wait(
        EndpointName=ENDPOINT_NAME,
        WaiterConfig={"Delay": 30, "MaxAttempts": 40},
    )

    elapsed = time.time() - start
    print(f"\n✅ Endpoint updated in {elapsed / 60:.1f} minutes!")
    print(f"\nThe endpoint now handles full audio files with chunking.")
    print(f"Lambda can send raw audio bytes — no need for Lambda-side librosa.\n")


if __name__ == "__main__":
    update()
