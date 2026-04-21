"""Device detection and model path resolution for the transcription service."""

import logging
import os

import torch

logger = logging.getLogger(__name__)

# Base model directory name used as a fallback for processor files
_FALLBACK_MODEL_DIR = "ai_models/whisper-small"


def _get_project_root() -> str:
    """Return the absolute path to the project root (3 levels up from this file)."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def resolve_model_paths(
    model_path: str = "ai_models/whisper-nepali-small",
) -> tuple[str, str]:
    """
    Resolve relative model paths to absolute paths.

    Returns:
        (full_model_path, fallback_model_path) — both absolute.

    Raises:
        FileNotFoundError: If the primary model directory does not exist.
    """
    root = _get_project_root()
    full_model_path = os.path.join(root, model_path)
    fallback_model_path = os.path.join(root, _FALLBACK_MODEL_DIR)

    if not os.path.exists(full_model_path):
        raise FileNotFoundError(f"Model directory not found at: {full_model_path}")

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
