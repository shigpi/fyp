"""
start_endpoint.py — Deploy the Whisper SageMaker real-time GPU endpoint.

Run this before a demo or test session:
    uv run python sagemaker/start_endpoint.py

Takes ~5-10 minutes. When the endpoint is live, uncomment
SAGEMAKER_ENDPOINT_NAME in .env and restart the backend.

Cost: ~$0.94/hr on ml.g4dn.xlarge while running.
Run stop_endpoint.py when done to stop billing immediately.
"""

import os
import sys
import tarfile
import time

import boto3
import sagemaker
from sagemaker.huggingface.model import HuggingFaceModel

# ── Configuration ──────────────────────────────────────────────────────────────
HF_MODEL_ID   = "kkarhm/whisper-nep-eng-codemixed-peft-small"
ENDPOINT_NAME = "voicescribe-whisper-endpoint"
INSTANCE_TYPE = "ml.g4dn.xlarge"   # 16 GB GPU VRAM, 4 vCPUs, ~$0.94/hr
REGION        = os.getenv("AWS_REGION", "ap-south-1")

# HuggingFace DLC versions to request
TRANSFORMERS_VERSION = "4.37.0"
PYTORCH_VERSION      = "2.1.0"
PY_VERSION           = "py310"

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
        key_prefix="voicescribe-whisper/code",
    )
    print(f"  → Uploaded to {s3_uri}")
    return s3_uri


def deploy():
    print("=" * 60)
    print("VoiceScribe — SageMaker GPU Endpoint Deployment")
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
            f"  SAGEMAKER_ROLE_ARN={role}\n"
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

    # ── Define HuggingFace Model ───────────────────────────────────────────────
    model = HuggingFaceModel(
        model_data=model_data,
        role=role,
        sagemaker_session=sm_session,
        transformers_version=TRANSFORMERS_VERSION,
        pytorch_version=PYTORCH_VERSION,
        py_version=PY_VERSION,
        env={
            "HF_MODEL_ID": HF_MODEL_ID,
            "HF_TASK": "automatic-speech-recognition",
        },
    )

    # ── Deploy Real-time Endpoint ──────────────────────────────────────────────
    print(f"Deploying '{ENDPOINT_NAME}' on {INSTANCE_TYPE} ...")
    print("This takes ~5-10 minutes ...\n")
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
    print(f"  1. Uncomment in .env:")
    print(f"       SAGEMAKER_ENDPOINT_NAME={ENDPOINT_NAME}")
    print(f"  2. Restart backend:")
    print(f"       uv run uvicorn backend.main:app --port 8000 --reload --host 0.0.0.0")
    print(f"  3. Test with:")
    print(f"       uv run python sagemaker/test_endpoint.py")
    print(f"  4. When done, stop billing:")
    print(f"       uv run python sagemaker/stop_endpoint.py\n")


if __name__ == "__main__":
    deploy()
