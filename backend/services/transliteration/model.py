import torch
import torch.nn as nn
import torch.nn.functional as F

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
    
    def init_decoder_hidden(self, h, c):
        """
        h,c: [layers*2, batch, hidden]
        """

        layers_times_2, batch, hidden = h.size()

        h = h.view(self.num_layers, 2, batch, hidden)
        c = c.view(self.num_layers, 2, batch, hidden)

        # concat forward + backward
        h = torch.cat([h[:, 0], h[:, 1]], dim=2)
        c = torch.cat([c[:, 0], c[:, 1]], dim=2)

        # project to decoder size
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
        # Forward pass is not strictly needed for inference
        pass

    def inference(self, source, max_len=50):
        self.eval()
        with torch.no_grad():
            outputs, h, c = self.encoder(source)
            h, c = self.decoder.init_decoder_hidden(h, c)

            # first input to decoder is <sos>
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
