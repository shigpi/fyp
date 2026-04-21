"""
start_endpoint.py — Deploy the Transliteration LSTM SageMaker endpoint.

Run this before using SageMaker-backed transliteration:
    python sagemaker/transliteration/start_endpoint.py

Takes ~3-5 minutes (CPU instance, much faster than GPU).
When the endpoint is live, set TRANSLITERATION_ENDPOINT_NAME in .env
and restart the backend.

Cost: ~$0.12/hr on ml.m5.large while running.
Run stop_endpoint.py when done to stop billing immediately.
"""

import os
import sys
import tarfile
import time

import boto3
import sagemaker
from sagemaker.pytorch.model import PyTorchModel

# ── Configuration ──────────────────────────────────────────────────────────────
HF_MODEL_ID   = "kkarhm/transliteration-lstm-nepali"
ENDPOINT_NAME = "voicescribe-transliteration-endpoint"
INSTANCE_TYPE = "ml.m5.large"   # CPU — LSTM is lightweight, ~$0.12/hr
REGION        = os.getenv("AWS_REGION", "ap-south-1")

# PyTorch DLC versions
PYTORCH_VERSION = "2.1.0"
PY_VERSION      = "py310"

# Path to custom inference code directory
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CODE_DIR     = os.path.join(_SCRIPT_DIR, "code")
TARBALL_PATH = os.path.join(_SCRIPT_DIR, "model.tar.gz")


def _bundle_code() -> str:
    """Package code/ into model.tar.gz (SageMaker picks up inference.py from it)."""
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
        key_prefix="voicescribe-transliteration/code",
    )
    print(f"  → Uploaded to {s3_uri}")
    return s3_uri


def deploy():
    print("=" * 60)
    print("VoiceScribe — SageMaker Transliteration Endpoint Deployment")
    print("=" * 60)
    print(f"  Region      : {REGION}")
    print(f"  Endpoint    : {ENDPOINT_NAME}")
    print(f"  Instance    : {INSTANCE_TYPE}")
    print(f"  HF model    : {HF_MODEL_ID}")
    print()

    boto_session = boto3.Session(region_name=REGION)
    sm_session   = sagemaker.Session(boto_session=boto_session)

    # ── IAM Role ───────────────────────────────────────────────────────────────
    role = os.getenv("SAGEMAKER_ROLE_ARN", "").strip()
    if not role:
        print(
            "SAGEMAKER_ROLE_ARN is not set.\n"
            "Set it in .env, e.g.:\n"
            "  SAGEMAKER_ROLE_ARN=arn:aws:iam::...\n"
        )
        role = input("Paste your SageMaker IAM Role ARN now: ").strip()
        if not role.startswith("arn:aws:iam::"):
            print("Invalid ARN format. Exiting.")
            sys.exit(1)

    print(f"  IAM Role    : {role}")
    print()

    # ── Bundle & Upload custom inference code ──────────────────────────────────
    _bundle_code()
    model_data = _upload_to_s3(sm_session)
    print()

    # ── Define PyTorch Model ───────────────────────────────────────────────────
    model = PyTorchModel(
        model_data=model_data,
        role=role,
        sagemaker_session=sm_session,
        framework_version=PYTORCH_VERSION,
        py_version=PY_VERSION,
        env={
            "HF_MODEL_ID": HF_MODEL_ID,
        },
    )

    # ── Deploy Real-time Endpoint ──────────────────────────────────────────────
    print(f"Deploying '{ENDPOINT_NAME}' on {INSTANCE_TYPE} ...")
    print("This takes ~3-5 minutes ...\n")
    start = time.time()

    model.deploy(
        initial_instance_count=1,
        instance_type=INSTANCE_TYPE,
        endpoint_name=ENDPOINT_NAME,
        wait=True,
    )

    elapsed = time.time() - start
    print(f"\n✅ Endpoint live in {elapsed / 60:.1f} minutes!")
    print(f"\nNext steps:")
    print(f"  1. Set in .env:")
    print(f"       TRANSLITERATION_ENDPOINT_NAME={ENDPOINT_NAME}")
    print(f"  2. Restart backend:")
    print(f"       uv run uvicorn backend.main:app --port 8000 --reload --host 0.0.0.0")
    print(f"  3. Test with:")
    print(f"       python sagemaker/transliteration/test_endpoint.py")
    print(f"  4. When done, stop billing:")
    print(f"       python sagemaker/transliteration/stop_endpoint.py\n")


if __name__ == "__main__":
    deploy()
