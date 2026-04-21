"""Whisper model and processor loading utilities."""

import logging

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

logger = logging.getLogger(__name__)


def load_processor(model_path: str, fallback_path: str) -> AutoProcessor:
    """
    Load the Whisper processor, falling back to the base model directory
    if the primary path is missing tokenizer/processor files.

    Args:
        model_path: Primary (fine-tuned) model directory.
        fallback_path: Base whisper-small directory for fallback.

    Returns:
        An AutoProcessor instance.
    """
    try:
        logger.info("Loading processor from primary path: %s", model_path)
        return AutoProcessor.from_pretrained(model_path, local_files_only=True)
    except (FileNotFoundError, TypeError, Exception):
        logger.warning(
            "Primary processor files incomplete — falling back to: %s", fallback_path
        )
        return AutoProcessor.from_pretrained(fallback_path, local_files_only=True)


def load_model(
    model_path: str,
    device: str,
    dtype: torch.dtype,
) -> AutoModelForSpeechSeq2Seq:
    """
    Load the Whisper speech-to-text model.

    Args:
        model_path: Directory containing the model weights.
        device: Target device string ("cpu", "cuda", "mps").
        dtype: Torch data type matching the device.

    Returns:
        The model moved to the target device in eval mode.

    Note:
        PEFT adapter loading is not currently active. To re-enable it,
        load a base model via ``WhisperForConditionalGeneration.from_pretrained``
        and then apply ``PeftModel.from_pretrained(base_model, adapter_path)``.
    """
    logger.info("Loading model from: %s", model_path)

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_path,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        local_files_only=True,
    ).to(device)

    model.eval()
    logger.info("Model loaded successfully on %s.", device)
    return model
