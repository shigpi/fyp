"""Device detection and model path resolution for the transliteration service."""

import logging
import os
import torch

logger = logging.getLogger(__name__)

# HuggingFace repo ID for auto-download
_HF_REPO_ID = "kkarhm/transliteration-lstm-nepali"

# Default relative path from the project root
_DEFAULT_MODEL_PATH = "ai_models/transliteration-model/model.pt"


def _get_project_root() -> str:
    """Return the absolute path to the project root (3 levels up from this file)."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def _download_model(local_dir: str) -> None:
    """
    Download model.pt from HuggingFace Hub into *local_dir*.

    Creates the target directory automatically.
    """
    from huggingface_hub import hf_hub_download

    logger.info(
        "Transliteration model not found locally — downloading '%s' into %s …",
        _HF_REPO_ID,
        local_dir,
    )
    os.makedirs(local_dir, exist_ok=True)
    hf_hub_download(
        repo_id=_HF_REPO_ID,
        filename="model.pt",
        local_dir=local_dir,
    )
    logger.info("Download complete: %s", local_dir)


def resolve_model_path(model_path: str = _DEFAULT_MODEL_PATH) -> str:
    """
    Resolve relative model paths to absolute paths.

    If the model file does not exist, it is automatically downloaded
    from HuggingFace Hub.

    Returns:
        full_model_path (absolute).
    """
    root = _get_project_root()
    full_model_path = os.path.join(root, model_path)

    if not os.path.exists(full_model_path):
        model_dir = os.path.dirname(full_model_path)
        _download_model(model_dir)

    logger.info("Model path resolved: %s", full_model_path)
    return full_model_path


def detect_device() -> torch.device:
    """
    Select the best available compute device.
    
    Returns:
        torch.device
    """
    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    logger.info("Using device: %s", device)
    return device
