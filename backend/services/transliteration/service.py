"""Transliteration service acting as a singleton.

Supports two modes selected via the TRANSLITERATION_ENDPOINT_NAME env var:

  • SageMaker mode  — set TRANSLITERATION_ENDPOINT_NAME; text is sent to
                      the GPU/CPU endpoint for transliteration.
  • Local mode      — model is loaded into memory (original behaviour);
                      used when TRANSLITERATION_ENDPOINT_NAME is not set.

If SageMaker mode is selected but the endpoint is unreachable at startup,
the service automatically falls back to local mode (provided the local
model files exist under ai_models/).
"""

import logging
import os
import re

logger = logging.getLogger(__name__)


class TransliterationService:
    _instance = None

    def __init__(self):
        if TransliterationService._instance is not None:
            raise Exception("This class is a singleton!")
        TransliterationService._instance = self

        endpoint_name = os.getenv("TRANSLITERATION_ENDPOINT_NAME", "").strip()

        if endpoint_name:
            if self._try_sagemaker(endpoint_name):
                return  # SageMaker mode ready

            # SageMaker unreachable — fall back to local
            logger.warning(
                "⚠️  SageMaker transliteration endpoint '%s' is unreachable. "
                "Falling back to local model.",
                endpoint_name,
            )
            self._init_local_safe()
        else:
            # No endpoint configured — go straight to local
            self._init_local_safe()

    # ── SageMaker probe ───────────────────────────────────────────────────────

    def _try_sagemaker(self, endpoint_name: str) -> bool:
        """Try to initialise SageMaker mode and verify the endpoint is reachable."""
        region = os.getenv("AWS_REGION", "ap-south-1")
        try:
            from .sagemaker_client import SageMakerTransliterationClient
            import boto3

            # Probe: describe the endpoint to check if it exists and is in service
            sm = boto3.client("sagemaker", region_name=region)
            resp = sm.describe_endpoint(EndpointName=endpoint_name)
            status = resp.get("EndpointStatus", "Unknown")
            if status != "InService":
                logger.warning(
                    "SageMaker endpoint '%s' exists but status is '%s' (not InService).",
                    endpoint_name, status,
                )
                return False

            self._sm_client = SageMakerTransliterationClient(endpoint_name, region)
            self._mode = "sagemaker"
            self.model = None
            logger.info(
                "✅  TransliterationService using SageMaker endpoint: %s (%s)",
                endpoint_name, region,
            )
            return True
        except Exception as exc:
            logger.warning("SageMaker probe failed: %s", exc)
            return False

    # ── Local mode init (safe — won't crash the app) ──────────────────────────

    def _init_local_safe(self):
        """Attempt local model init; on failure set mode to 'unavailable'."""
        try:
            import torch
            from .config import resolve_model_path, detect_device
            from .exceptions import ModelNotLoadedError

            self._mode = "local"
            self.model = None
            self.device = detect_device()
            self.src_stoi = {}
            self.tgt_stoi = {}
            self.src_itos = {}
            self.tgt_itos = {}
            self._load_model()
            logger.info("✅  TransliterationService initialised in local mode.")
        except Exception as exc:
            self._mode = "unavailable"
            self.model = None
            logger.error(
                "❌  Transliteration service unavailable: local model failed to load (%s).",
                exc,
            )

    @staticmethod
    def get_instance():
        if TransliterationService._instance is None:
            TransliterationService()
        return TransliterationService._instance

    # ── Local mode helpers ────────────────────────────────────────────────────

    def _load_model(self):
        import torch
        from .config import resolve_model_path
        from .exceptions import ModelNotLoadedError
        from .model import LSTMEncoder, LSTMDecoder, LSTMSeq2Seq

        try:
            model_path = resolve_model_path()
        except FileNotFoundError as e:
            logger.error(str(e))
            return

        logger.info("Loading transliteration model...")
        try:
            ckpt = torch.load(model_path, map_location=self.device)

            self.src_stoi = ckpt['src_stoi']
            self.tgt_stoi = ckpt['tgt_stoi']
            self.src_itos = ckpt['src_itos']
            self.tgt_itos = ckpt['tgt_itos']
            config = ckpt['config']

            embed_size = config['embed_size']
            hidden_size = config['hidden_size']
            src_vocab_size = len(self.src_stoi)
            tgt_vocab_size = len(self.tgt_stoi)
            num_layers = 2
            p = 0.2

            encoder = LSTMEncoder(src_vocab_size, embed_size, hidden_size, num_layers, p)
            decoder = LSTMDecoder(tgt_vocab_size, embed_size, hidden_size, num_layers, p)

            self.model = LSTMSeq2Seq(encoder, decoder, self.device, self.tgt_stoi).to(self.device)
            self.model.load_state_dict(ckpt['model_state_dict'])
            self.model.eval()
            logger.info("Transliteration model loaded successfully.")
        except Exception as e:
            logger.error("Failed to load transliteration model: %s", e)
            from .exceptions import ModelNotLoadedError
            raise ModelNotLoadedError(str(e)) from e

    def _transliterate_word(self, word: str, max_length=50) -> str:
        import torch

        if self.model is None:
            return word

        tokens = []
        for char in list(word):
            if char in self.src_stoi:
                tokens.append(self.src_stoi[char])
            else:
                tokens.append(self.src_stoi.get('<unk>', 0))

        input_tensor = torch.tensor(
            [self.src_stoi.get('<sos>', 1)] + tokens + [self.src_stoi.get('<eos>', 2)]
        ).unsqueeze(0).to(self.device)

        generated = self.model.inference(input_tensor, max_len=max_length)
        decoded_chars = [self.tgt_itos[i] for i in generated]
        return "".join(decoded_chars)

    def _transliterate_local(self, text: str) -> str:
        """Original local transliteration logic."""
        if self.model is None:
            return text

        words = text.split()
        transliterated_words = []
        for word in words:
            if re.match(r'^[A-Za-z]+$', word) or re.match(r'^[\u0900-\u097F]+$', word):
                transliterated_words.append(self._transliterate_word(word))
            else:
                transliterated_words.append(word)
        return " ".join(transliterated_words)

    # ── Public API ────────────────────────────────────────────────────────────

    def transliterate_word(self, word: str, max_length=50) -> str:
        if self._mode == "sagemaker":
            return self._sm_client.transliterate(word)
        return self._transliterate_word(word, max_length)

    def transliterate(self, text: str) -> str:
        if self._mode == "unavailable":
            logger.warning("Transliteration requested but service is unavailable; returning raw text.")
            return text
        if self._mode == "sagemaker":
            return self._sm_client.transliterate(text)
        return self._transliterate_local(text)
