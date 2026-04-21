"""
SageMaker custom inference handler for the VoiceScribe LSTM transliteration model.

Entry points:
  model_fn   — called once at container startup to load model + vocabularies
  input_fn   — deserialises the JSON request body into text
  predict_fn — runs LSTM seq2seq inference and returns transliteration
  output_fn  — serialises the prediction to JSON

The model is downloaded from HuggingFace Hub at startup (HF_MODEL_ID env var).
"""

import json
import logging
import os
import re

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


# ── Model Architecture (copied from backend/services/transliteration/model.py) ─


class LSTMEncoder(nn.Module):
    def __init__(self, vocab_size, embed_size, hidden_size, num_layers, p):
        super(LSTMEncoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_size, padding_idx=0)
        self.dropout = nn.Dropout(p)
        self.rnn = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True, bidirectional=True)

    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        outputs, (hidden, cell) = self.rnn(embedded)
        return outputs, hidden, cell


class BahdanauAttention(nn.Module):
    def __init__(self, hidden_size):
        super(BahdanauAttention, self).__init__()
        self.W1 = nn.Linear(hidden_size * 2, hidden_size)
        self.W2 = nn.Linear(hidden_size, hidden_size)
        self.V = nn.Linear(hidden_size, 1)

    def forward(self, hidden, encoder_outputs):
        score = self.V(torch.tanh(self.W1(encoder_outputs) + self.W2(hidden).unsqueeze(1)))
        attention_weights = F.softmax(score, dim=1)
        context_vector = attention_weights * encoder_outputs
        context_vector = torch.sum(context_vector, dim=1)
        return context_vector, attention_weights


class LSTMDecoder(nn.Module):
    def __init__(self, vocab_size, embed_size, hidden_size, num_layers, p):
        super(LSTMDecoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_size, padding_idx=0)
        self.dropout = nn.Dropout(p)
        self.attention = BahdanauAttention(hidden_size)

        self.num_layers = num_layers

        self.rnn = nn.LSTM(embed_size + hidden_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)

        self.enc2dec_h = nn.Linear(hidden_size * 2, hidden_size)
        self.enc2dec_c = nn.Linear(hidden_size * 2, hidden_size)
        self.attn2dec = nn.Linear(hidden_size * 2, hidden_size)

    def forward(self, x, hidden, cell, encoder_outputs):
        x = x.unsqueeze(1)
        embedded = self.dropout(self.embedding(x))

        top_hidden = hidden[-1]
        context_vector, attention_weights = self.attention(top_hidden, encoder_outputs)
        context_vector = self.attn2dec(context_vector)

        rnn_input = torch.cat([embedded, context_vector.unsqueeze(1)], dim=2)
        output, (hidden, cell) = self.rnn(rnn_input, (hidden, cell))
        prediction = self.fc(output.squeeze(1))

        return prediction, hidden, cell

    def init_decoder_hidden(self, h, c):
        layers_times_2, batch, hidden = h.size()
        h = h.view(self.num_layers, 2, batch, hidden)
        c = c.view(self.num_layers, 2, batch, hidden)
        h = torch.cat([h[:, 0], h[:, 1]], dim=2)
        c = torch.cat([c[:, 0], c[:, 1]], dim=2)
        h = torch.tanh(self.enc2dec_h(h))
        c = torch.tanh(self.enc2dec_c(c))
        return h, c


class LSTMSeq2Seq(nn.Module):
    def __init__(self, encoder, decoder, device, tgt_stoi):
        super(LSTMSeq2Seq, self).__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.device = device
        self.tgt_stoi = tgt_stoi

    def forward(self, source, target, teacher_forcing_ratio=0.5):
        pass

    def inference(self, source, max_len=50):
        self.eval()
        with torch.no_grad():
            outputs, h, c = self.encoder(source)
            h, c = self.decoder.init_decoder_hidden(h, c)

            sos_idx = self.tgt_stoi.get('<sos>', 1)
            eos_idx = self.tgt_stoi.get('<eos>', 2)

            x = torch.tensor([sos_idx], device=self.device)
            generated = []

            for _ in range(max_len):
                prediction, h, c = self.decoder(x, h, c, outputs)
                predicted_class = prediction.argmax(1).item()

                if predicted_class == eos_idx:
                    break

                generated.append(predicted_class)
                x = torch.tensor([predicted_class], device=self.device)

            return generated


# ── SageMaker Entry Points ─────────────────────────────────────────────────────


def model_fn(model_dir, context=None):
    """
    Load the transliteration LSTM from HuggingFace Hub.

    The HF_MODEL_ID environment variable points to the uploaded model repo.
    We download model.pt and reconstruct the full seq2seq model.

    Returns:
        dict with keys "model", "src_stoi", "tgt_stoi", "src_itos", "tgt_itos".
    """
    from huggingface_hub import hf_hub_download

    model_id = os.environ.get("HF_MODEL_ID", "kkarhm/transliteration-lstm-nepali")
    logger.info("Loading transliteration model from HF Hub: %s", model_id)

    model_path = hf_hub_download(repo_id=model_id, filename="model.pt")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(model_path, map_location=device)

    src_stoi = ckpt["src_stoi"]
    tgt_stoi = ckpt["tgt_stoi"]
    src_itos = ckpt["src_itos"]
    tgt_itos = ckpt["tgt_itos"]
    config = ckpt["config"]

    embed_size = config["embed_size"]
    hidden_size = config["hidden_size"]
    src_vocab_size = len(src_stoi)
    tgt_vocab_size = len(tgt_stoi)
    num_layers = 2
    p = 0.2

    encoder = LSTMEncoder(src_vocab_size, embed_size, hidden_size, num_layers, p)
    decoder = LSTMDecoder(tgt_vocab_size, embed_size, hidden_size, num_layers, p)

    model = LSTMSeq2Seq(encoder, decoder, device, tgt_stoi).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    logger.info("Transliteration model loaded on %s.", device)
    return {
        "model": model,
        "device": device,
        "src_stoi": src_stoi,
        "tgt_stoi": tgt_stoi,
        "src_itos": src_itos,
        "tgt_itos": tgt_itos,
    }


def input_fn(request_body, request_content_type):
    """
    Deserialise the JSON request: {"text": "..."} → dict.

    Returns:
        dict with key "text".
    """
    if request_content_type != "application/json":
        raise ValueError(f"Unsupported content type: {request_content_type}. Expected application/json.")

    data = json.loads(request_body)
    text = data.get("text", "")
    logger.info("Input text (%d chars): %s", len(text), text[:80])
    return {"text": text}


def predict_fn(input_data, model_artifacts):
    """
    Transliterate word-by-word using the LSTM seq2seq model.

    Returns:
        dict with "transliterated_text".
    """
    text = input_data["text"]
    model = model_artifacts["model"]
    device = model_artifacts["device"]
    src_stoi = model_artifacts["src_stoi"]
    tgt_itos = model_artifacts["tgt_itos"]

    def transliterate_word(word, max_length=50):
        tokens = []
        for char in list(word):
            if char in src_stoi:
                tokens.append(src_stoi[char])
            else:
                tokens.append(src_stoi.get("<unk>", 0))

        input_tensor = torch.tensor(
            [src_stoi.get("<sos>", 1)] + tokens + [src_stoi.get("<eos>", 2)]
        ).unsqueeze(0).to(device)

        generated = model.inference(input_tensor, max_len=max_length)
        decoded_chars = [tgt_itos[i] for i in generated]
        return "".join(decoded_chars)

    words = text.split()
    transliterated_words = []
    for word in words:
        if re.match(r"^[A-Za-z]+$", word) or re.match(r"^[\u0900-\u097F]+$", word):
            transliterated_words.append(transliterate_word(word))
        else:
            transliterated_words.append(word)

    result = " ".join(transliterated_words)
    logger.info("Transliteration result: %s", result[:80])
    return {"transliterated_text": result}


def output_fn(prediction, accept):
    """Serialise the prediction dict to JSON."""
    return json.dumps(prediction), "application/json"
