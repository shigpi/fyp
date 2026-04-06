"""Transliteration service acting as a singleton."""

import logging
import re
import torch

from .config import resolve_model_path, detect_device
from .exceptions import ModelNotLoadedError
from .model import LSTMEncoder, LSTMDecoder, LSTMSeq2Seq

logger = logging.getLogger(__name__)

class TransliterationService:
    _instance = None

    def __init__(self):
        if TransliterationService._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            TransliterationService._instance = self
            self.model = None
            self.device = detect_device()
            self.src_stoi = {}
            self.tgt_stoi = {}
            self.src_itos = {}
            self.tgt_itos = {}
            self._load_model()

    @staticmethod
    def get_instance():
        if TransliterationService._instance is None:
            TransliterationService()
        return TransliterationService._instance

    def _load_model(self):
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
            raise ModelNotLoadedError(str(e)) from e

    def transliterate_word(self, word: str, max_length=50) -> str:
        if self.model is None:
            return word

        tokens = []
        for char in list(word):
            if char in self.src_stoi:
                tokens.append(self.src_stoi[char])
            else:
                tokens.append(self.src_stoi.get('<unk>', 0))
                
        input_tensor = torch.tensor([self.src_stoi.get('<sos>', 1)] + tokens + [self.src_stoi.get('<eos>', 2)]).unsqueeze(0).to(self.device)
        
        generated = self.model.inference(input_tensor, max_len=max_length)
        
        decoded_chars = [self.tgt_itos[i] for i in generated]
                
        return "".join(decoded_chars)

    def transliterate(self, text: str) -> str:
        if self.model is None:
            return text

        words = text.split()
        transliterated_words = []
        for word in words:
            # We skip transliteration for symbols or numbers if desired
            if re.match(r'^[A-Za-z]+$', word) or re.match(r'^[\u0900-\u097F]+$', word):
                transliterated_words.append(self.transliterate_word(word))
            else:
                transliterated_words.append(word)
        return " ".join(transliterated_words)
