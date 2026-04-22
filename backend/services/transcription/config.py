"""Device detection and model path resolution for the transcription service."""

import logging
import os

import torch

logger = logging.getLogger(__name__)

# HuggingFace repo IDs for auto-download
_HF_PRIMARY_REPO = "kkarhm/whisper-nep-eng-codemixed-small"
_HF_FALLBACK_REPO = "openai/whisper-small"

# Relative directory paths under the project root
_PRIMARY_MODEL_DIR = "ai_models/whisper-nepali-small"
_FALLBACK_MODEL_DIR = "ai_models/whisper-small"


def _get_project_root() -> str:
    """Return the absolute path to the project root (3 levels up from this file)."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def _download_model(repo_id: str, local_dir: str) -> None:
    """
    Download a model from HuggingFace Hub into *local_dir*.

    Creates the target directory automatically. Uses snapshot_download
    so the full model (weights, config, tokenizer, etc.) is fetched.
    """
    from huggingface_hub import snapshot_download

    logger.info(
        "Model not found locally — downloading '%s' into %s  (this may take a while) …",
        repo_id,
        local_dir,
    )
    os.makedirs(local_dir, exist_ok=True)
    snapshot_download(repo_id=repo_id, local_dir=local_dir)
    logger.info("Download complete: %s", local_dir)


def resolve_model_paths(
    model_path: str = _PRIMARY_MODEL_DIR,
) -> tuple[str, str]:
    """
    Resolve relative model paths to absolute paths.

    If the directories do not exist, the models are automatically
    downloaded from HuggingFace Hub.

    Returns:
        (full_model_path, fallback_model_path) — both absolute.
    """
    root = _get_project_root()
    full_model_path = os.path.join(root, model_path)
    fallback_model_path = os.path.join(root, _FALLBACK_MODEL_DIR)

    if not os.path.exists(full_model_path):
        _download_model(_HF_PRIMARY_REPO, full_model_path)

    if not os.path.exists(fallback_model_path):
        _download_model(_HF_FALLBACK_REPO, fallback_model_path)

    logger.info("Model path resolved: %s", full_model_path)
    return full_model_path, fallback_model_path


def detect_device() -> tuple[str, torch.dtype]:
    """
    Select the best available compute device and matching dtype.

    Priority: CUDA → MPS (only if WHISPER_FORCE_CPU=false) → CPU.

    Returns:
        (device_name, torch_dtype)
    """
    force_cpu = os.getenv("WHISPER_FORCE_CPU", "true").lower() == "true"

    if torch.cuda.is_available():
        device, dtype = "cuda", torch.float16
    elif not force_cpu and torch.backends.mps.is_available():
        device = os.getenv("WHISPER_DEVICE", "mps")
        dtype = torch.float16
    else:
        device, dtype = "cpu", torch.float32

    logger.info("Using device: %s with dtype: %s", device, dtype)
    return device, dtype
