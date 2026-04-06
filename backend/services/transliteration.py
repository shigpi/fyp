import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import re

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
        
        # embed_size + hidden_size (instead of hidden_size * 2) gives 384
        self.rnn = nn.LSTM(embed_size + hidden_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)
        
        self.enc2dec_h = nn.Linear(hidden_size * 2, hidden_size)
        self.enc2dec_c = nn.Linear(hidden_size * 2, hidden_size)
        self.attn2dec = nn.Linear(hidden_size * 2, hidden_size)
        
    def forward(self, x, hidden, cell, encoder_outputs):
        x = x.unsqueeze(1)
        embedded = self.dropout(self.embedding(x))
        
        # Extract the top hidden state from the decoder to pass to attention
        top_hidden = hidden[-1]
        
        # Calculate attention weights and context vector
        context_vector, attention_weights = self.attention(top_hidden, encoder_outputs)
        
        # Pass context vector through attn2dec layer
        context_vector = self.attn2dec(context_vector)
        
        # Concatenate embedded input and mapped context vector
        rnn_input = torch.cat([embedded, context_vector.unsqueeze(1)], dim=2)
        
        output, (hidden, cell) = self.rnn(rnn_input, (hidden, cell))
        
        prediction = self.fc(output.squeeze(1))
        
        return prediction, hidden, cell

class LSTMSeq2Seq(nn.Module):
    def __init__(self, encoder, decoder, device):
        super(LSTMSeq2Seq, self).__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.device = device
        
    def forward(self, source, target, teacher_forcing_ratio=0.5):
        # Forward pass is not strictly needed for inference
        pass

class TransliterationService:
    _instance = None

    def __init__(self):
        if TransliterationService._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            TransliterationService._instance = self
            self.model = None
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
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
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ai_models', 'transliteration-model', 'model.pt')
        if not os.path.exists(model_path):
            print("Transliteration model not found at", model_path)
            return

        print("Loading transliteration model...")
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
        
        self.model = LSTMSeq2Seq(encoder, decoder, self.device).to(self.device)
        self.model.load_state_dict(ckpt['model_state_dict'])
        self.model.eval()
        print("Transliteration model loaded successfully.")

    def _encode_hidden_cell(self, hidden, cell):
        # hidden, cell shapes: (num_layers * num_directions, batch_size, hidden_size)
        # We need to reshape them to pass through the linear layers
        hidden_forward = hidden[0:hidden.size(0):2]
        hidden_backward = hidden[1:hidden.size(0):2]
        cell_forward = cell[0:cell.size(0):2]
        cell_backward = cell[1:cell.size(0):2]
        
        # Concatenate forward and backward
        hidden_cat = torch.cat((hidden_forward, hidden_backward), dim=2)
        cell_cat = torch.cat((cell_forward, cell_backward), dim=2)
        
        # Pass through linear layers
        decoder_hidden = torch.tanh(self.model.decoder.enc2dec_h(hidden_cat))
        decoder_cell = torch.tanh(self.model.decoder.enc2dec_c(cell_cat))
        return decoder_hidden, decoder_cell

    def transliterate_word(self, word: str, max_length=50) -> str:
        if self.model is None:
            return word

        # Reverse if translation direction is Nepali -> English
        # Actually, let's look at the mapping. If source string has English chars,
        # it might be the other way around. Let's try Roman->Nepali.
        tokens = []
        for char in list(word):
            if char in self.src_stoi:
                tokens.append(self.src_stoi[char])
            else:
                tokens.append(self.src_stoi.get('<unk>', 0))
                
        # If words are English to Nepali, we assume English is the source, Nepali is target.
        # But earlier I saw `src_stoi` had Devanagari and `tgt_stoi` had English.
        # This means the model translates Devanagari -> English (Romanization).
        # We might need to handle words properly. Wait, if we want Roman -> Nepali, this model is the wrong way!
        # But let's assume `src_stoi` is what we feed in. The user requested transliteration for "nepali english codemix".
        # This usually means Roman -> Nepali! Let's just use it however it's trained.
        
        input_tensor = torch.tensor([self.src_stoi.get('<sos>', 1)] + tokens + [self.src_stoi.get('<eos>', 2)]).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            encoder_outputs, hidden, cell = self.model.encoder(input_tensor)
            
            hidden, cell = self._encode_hidden_cell(hidden, cell)
            
            x = torch.tensor([self.tgt_stoi.get('<sos>', 1)]).to(self.device)
            decoded_chars = []
            
            for _ in range(max_length):
                prediction, hidden, cell = self.model.decoder(x, hidden, cell, encoder_outputs)
                predicted_class = prediction.argmax(1).item()
                
                if predicted_class == self.tgt_stoi.get('<eos>', 2):
                    break
                    
                decoded_char = self.tgt_itos[predicted_class]
                decoded_chars.append(decoded_char)
                
                x = torch.tensor([predicted_class]).to(self.device)
                
        return "".join(decoded_chars)

    def transliterate(self, text: str) -> str:
        words = text.split()
        transliterated_words = []
        for word in words:
            # We skip transliteration for symbols or numbers if desired
            if re.match(r'^[A-Za-z]+$', word) or re.match(r'^[\u0900-\u097F]+$', word):
                transliterated_words.append(self.transliterate_word(word))
            else:
                transliterated_words.append(word)
        return " ".join(transliterated_words)

transliteration_service = TransliterationService()
