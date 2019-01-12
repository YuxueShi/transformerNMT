# -*- coding: utf-8 -*-

import math

import torch
import torch.nn as nn


def positional_encoding(embedding_dim, max_len=1000):
    pe = torch.zeros(max_len, embedding_dim)
    position = torch.arange(max_len).unsqueeze(1).float()
    div_term = torch.exp(torch.arange(0, embedding_dim, 2).float() * -(math.log(10000.0) / embedding_dim))
    pe[:, 0::2] = torch.sin(position * div_term)
    pe[:, 1::2] = torch.cos(position * div_term)
    return pe


class Embedding(nn.Module):
    def __init__(self, embedding_dim, vocab_size, padding_idx, dropout=0):
        self.word_padding_idx = padding_idx
        self.embedding_dim = embedding_dim
        pe = positional_encoding(embedding_dim)
        super(Embedding, self).__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=padding_idx)
        self.register_buffer('pe', pe)
        self.dropout = nn.Dropout(p=dropout)

        self.reset_parameters()

    def reset_parameters(self):
        nn.init.normal_(self.embedding.weight, mean=0, std=self.embedding_dim ** -0.5)
        nn.init.constant_(self.embedding.weight[self.padding_idx], 0.)

    @property
    def padding_idx(self):
        return self.word_padding_idx

    def forward(self, x, timestep=0):
        embedding = self.embedding(x) * (self.embedding_dim ** 0.5) + self.pe[timestep:timestep + x.size(1)]
        return self.dropout(embedding)

    @classmethod
    def make_embedding(cls, opt, field, embedding_dim):
        word_padding_idx = field.pad_id
        vocab_size = len(field.vocab)
        return cls(embedding_dim=embedding_dim,
                   dropout=opt.dropout,
                   padding_idx=word_padding_idx,
                   vocab_size=vocab_size)

