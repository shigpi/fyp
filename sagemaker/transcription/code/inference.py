"""
SageMaker custom inference handler for kkarhm/whisper-nep-eng-codemixed-small.

Entry points:
  model_fn   — called once at container startup to load model + processor
  input_fn   — deserialises the raw request body into audio data
  predict_fn — runs Whisper inference (with chunking for long audio)
  output_fn  — serialises the prediction to JSON
"""

import io
import json
import logging
import os

import librosa
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
_TARGET_SR = 16_000
_CHUNK_LENGTH_S = 30.0
_OVERLAP_S = 1.0          # 1s overlap for context continuity
_MIN_CHUNK_S = 0.5        # skip chunks shorter than 0.5s
_SUPPORTED_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "application/octet-stream",
}


# ── model_fn ───────────────────────────────────────────────────────────────────

def model_fn(model_dir: str, context=None):
    """
    Load the Whisper model and processor from the HuggingFace Hub.

    SageMaker calls this once at container startup. The HF_MODEL_ID
    environment variable is set by the deploy script.

    Returns:
        dict with keys "model" and "processor".
    """
    model_id = os.environ.get(
        "HF_MODEL_ID", "kkarhm/whisper-nep-eng-codemixed-small"
    )
    logger.info("Loading model: %s", model_id)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    logger.info("Device: %s, dtype: %s", device, dtype)

    try:
        processor = AutoProcessor.from_pretrained(model_id)
    except Exception as exc:
        logger.warning(
            "Could not load processor from %s: %s. Falling back to 'openai/whisper-small'.",
            model_id, exc
        )
        processor = AutoProcessor.from_pretrained("openai/whisper-small")
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    ).to(device)
    model.eval()

    logger.info("Model loaded successfully on %s.", device)
    return {"model": model, "processor": processor, "device": device, "dtype": dtype}


# ── input_fn ───────────────────────────────────────────────────────────────────

def input_fn(request_body, request_content_type):
    """
    Deserialise the raw audio bytes sent by the Lambda backend.

    The backend sends the entire audio file as raw bytes.
    We resample to 16 kHz mono float32 and return a numpy array.

    Returns:
        dict with "audio" (np.ndarray) and "duration" (float seconds).
    """
    if request_content_type not in _SUPPORTED_CONTENT_TYPES:
        raise ValueError(
            f"Unsupported content type: {request_content_type}. "
            f"Supported: {_SUPPORTED_CONTENT_TYPES}"
        )

    audio_bytes = io.BytesIO(request_body)

    try:
        audio_data, sr = librosa.load(audio_bytes, sr=_TARGET_SR, mono=True)
    except Exception as exc:
        raise ValueError(f"Failed to decode audio: {exc}") from exc

    # Normalise amplitude to [-1, 1]
    max_val = np.abs(audio_data).max()
    if max_val > 0:
        audio_data = audio_data / max_val

    duration = len(audio_data) / _TARGET_SR

    logger.info(
        "Input audio: duration=%.2fs, sr=%d, samples=%d",
        duration, _TARGET_SR, len(audio_data),
    )

    return {"audio": audio_data, "duration": duration}


# ── Audio chunking ─────────────────────────────────────────────────────────────

def _chunk_audio(audio_data: np.ndarray) -> list:
    """Split audio into overlapping chunks for Whisper's 30s context window."""
    chunk_samples = int(_CHUNK_LENGTH_S * _TARGET_SR)
    overlap_samples = int(_OVERLAP_S * _TARGET_SR)
    stride = chunk_samples - overlap_samples

    total_samples = len(audio_data)
    if total_samples <= chunk_samples:
        return [audio_data]

    chunks = []
    for start_idx in range(0, total_samples, stride):
        end_idx = min(start_idx + chunk_samples, total_samples)
        chunk = audio_data[start_idx:end_idx]
        # Skip tiny trailing chunks
        if len(chunk) >= int(_MIN_CHUNK_S * _TARGET_SR):
            chunks.append(chunk)
        if end_idx == total_samples:
            break

    return chunks


def _is_hallucination(text: str) -> bool:
    """Detect common Whisper hallucination patterns."""
    t = text.strip()
    if not t:
        return True

    # Repeated short phrases (e.g., "Thank you. Thank you. Thank you.")
    words = t.split()
    if len(words) >= 6:
        # Check if the same 1-3 word pattern repeats more than 3 times
        for n in range(1, 4):
            if len(words) >= n * 4:
                pattern = " ".join(words[:n])
                count = 0
                for i in range(0, len(words) - n + 1, n):
                    if " ".join(words[i:i+n]) == pattern:
                        count += 1
                if count >= 4:
                    return True

    # Single repeated character or very short gibberish
    if len(set(t.replace(" ", ""))) <= 2 and len(t) > 10:
        return True

    return False


# ── predict_fn ─────────────────────────────────────────────────────────────────

def predict_fn(input_data, model_artifacts):
    """
    Run Whisper inference on the full audio, chunking if longer than 30s.

    Returns:
        dict with "transcription" (str) and "duration" (float seconds).
    """
    audio_data: np.ndarray = input_data["audio"]
    duration = input_data["duration"]

    model = model_artifacts["model"]
    processor = model_artifacts["processor"]
    device = model_artifacts["device"]
    dtype = model_artifacts["dtype"]

    # Generation kwargs — tuned to reduce hallucination
    gen_kwargs = {
        "max_new_tokens": 440,
        "return_timestamps": False,
        "num_beams": 1,
        "do_sample": False,
        "repetition_penalty": 1.3,      # stronger penalty to avoid loops
        "no_repeat_ngram_size": 4,       # prevent 4-gram repetitions
        "task": "transcribe",
        "forced_decoder_ids": None,
        "language": "nepali",
    }

    # Chunk the audio
    chunks = _chunk_audio(audio_data)
    logger.info("Processing %d chunk(s) for %.2fs audio", len(chunks), duration)

    full_transcription = []
    prev_text = ""

    for i, chunk in enumerate(chunks):
        # Skip very short chunks (< 0.5s)
        if len(chunk) < _TARGET_SR * _MIN_CHUNK_S:
            continue

        inputs = processor(chunk, sampling_rate=_TARGET_SR, return_tensors="pt")
        input_features = inputs.input_features.to(device=device, dtype=dtype)

        # Create attention mask to help model distinguish real audio from padding
        attention_mask = torch.ones(
            input_features.shape[:2], dtype=torch.long, device=device
        )

        with torch.no_grad():
            predicted_ids = model.generate(
                input_features,
                attention_mask=attention_mask,
                **gen_kwargs,
            )

        chunk_text = processor.batch_decode(
            predicted_ids, skip_special_tokens=True
        )[0].strip()

        # Skip hallucinated chunks
        if _is_hallucination(chunk_text):
            logger.debug("Chunk %d: skipped (hallucination detected: '%s')", i + 1, chunk_text[:60])
            continue

        # Deduplicate overlap: if this chunk starts with the end of the previous,
        # trim the overlapping portion
        if prev_text and chunk_text:
            chunk_text = _deduplicate_overlap(prev_text, chunk_text)

        if chunk_text:
            full_transcription.append(chunk_text)
            prev_text = chunk_text
            logger.debug("Chunk %d: %s", i + 1, chunk_text[:80])

    transcription = " ".join(full_transcription).strip()

    if not transcription:
        transcription = "[No speech detected]"

    logger.info("Transcription (%.2fs): %s", duration, transcription[:80])

    return {"transcription": transcription, "duration": duration}


def _deduplicate_overlap(prev: str, current: str) -> str:
    """
    Remove overlapping text between the end of the previous chunk
    and the start of the current chunk.
    """
    prev_words = prev.split()
    current_words = current.split()

    # Try matching the last N words of prev with the first N words of current
    max_overlap = min(len(prev_words), len(current_words), 8)

    for n in range(max_overlap, 0, -1):
        if prev_words[-n:] == current_words[:n]:
            # Remove the overlapping prefix from current
            return " ".join(current_words[n:])

    return current


# ── output_fn ──────────────────────────────────────────────────────────────────

def output_fn(prediction, accept):
    """Serialise the prediction dict to JSON."""
    return json.dumps(prediction), "application/json"
