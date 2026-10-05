import torch
import torch.nn as nn

class EToLSTMAttention(nn.Module):
    """
    ETo forecasting model using an LSTM with a learned attention mechanism.
    Originally designed for 14-day sequences of 12 weather features.
    """
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers, batch_first=True, dropout=dropout
        )
        self.attention = nn.Linear(hidden_size, 1)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, (h_n, c_n) = self.lstm(x)
        attn_weights = torch.softmax(self.attention(out), dim=1)
        out = torch.sum(attn_weights * out, dim=1)
        out = self.relu(self.fc1(out))
        out = self.dropout(out)
        out = self.fc2(out)
        return out.squeeze(1)

    def predict_with_attention(self, x: torch.Tensor):
        """Forward pass that also returns attention weights."""
        out, (h_n, c_n) = self.lstm(x)
        attn_weights = torch.softmax(self.attention(out), dim=1)
        context = torch.sum(attn_weights * out, dim=1)
        out = self.relu(self.fc1(context))
        out = self.dropout(out)
        out = self.fc2(out)
        return out.squeeze(1), attn_weights.squeeze(-1)
