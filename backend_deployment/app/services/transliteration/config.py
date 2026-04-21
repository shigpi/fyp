"""Device detection and model path resolution for the transliteration service."""

import logging
import os
import torch

logger = logging.getLogger(__name__)

def _get_project_root() -> str:
    """Return the absolute path to the project root (3 levels up from this file)."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )

def resolve_model_path(model_path: str = "ai_models/transliteration-model/model.pt") -> str:
    """
    Resolve relative model paths to absolute paths.

    Returns:
        full_model_path (absolute).

    Raises:
        FileNotFoundError: If the primary model file does not exist.
    """
    root = _get_project_root()
    full_model_path = os.path.join(root, model_path)

    if not os.path.exists(full_model_path):
        raise FileNotFoundError(f"Model file not found at: {full_model_path}")

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
