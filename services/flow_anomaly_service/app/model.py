from __future__ import annotations

import torch
from torch import nn


class LSTMAutoencoder(nn.Module):
    """2-layer LSTM Autoencoder for sequence reconstruction."""

    def __init__(
        self,
        input_size: int = 3,
        hidden_size: int = 128,
        latent_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.latent_size = latent_size
        self.num_layers = num_layers

        self.encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
        )
        self.to_latent_h = nn.Linear(hidden_size, latent_size)
        self.to_latent_c = nn.Linear(hidden_size, latent_size)

        self.from_latent_h = nn.Linear(latent_size, hidden_size)
        self.from_latent_c = nn.Linear(latent_size, hidden_size)

        self.decoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
        )
        self.output_layer = nn.Linear(hidden_size, input_size)

    def encode(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        _, (h_n, c_n) = self.encoder(x)
        h_last = h_n[-1]
        c_last = c_n[-1]
        return self.to_latent_h(h_last), self.to_latent_c(c_last)

    def decode(self, z_h: torch.Tensor, z_c: torch.Tensor, seq_len: int) -> torch.Tensor:
        batch_size = z_h.shape[0]
        h0_last = self.from_latent_h(z_h)
        c0_last = self.from_latent_c(z_c)

        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=z_h.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=z_c.device)
        h0[-1] = h0_last
        c0[-1] = c0_last

        decoder_input = torch.zeros(batch_size, seq_len, self.input_size, device=z_h.device)
        decoded, _ = self.decoder(decoder_input, (h0, c0))
        return self.output_layer(decoded)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq_len = x.shape[1]
        z_h, z_c = self.encode(x)
        return self.decode(z_h, z_c, seq_len)
