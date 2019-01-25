# -*- coding: utf-8 -*-

import torch
import torch.nn as nn
import torch.nn.functional as func
import torch.optim as optim


class WarmAdam(object):
    def __init__(self, params, lr, hidden_size, warm_up, init_step):
        self.original_lr = lr
        self.lr = lr
        self.n_step = init_step
        self.hidden_size = hidden_size
        self.warm_up_step = warm_up
        self.optimizer = optim.Adam(params, betas=[0.9, 0.98], eps=1e-9)

    def step(self):
        self.n_step += 1
        warm_up = min(self.n_step ** (-0.5), self.n_step * self.warm_up_step ** (-1.5))
        self.lr = self.original_lr * (self.hidden_size ** (-0.5) * warm_up)
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = self.lr
        self.optimizer.step()


class LabelSmoothingLoss(nn.Module):
    def __init__(self, label_smoothing, tgt_vocab_size, ignore_index):
        self.padding_idx = ignore_index
        self.label_smoothing = label_smoothing
        self.vocab = tgt_vocab_size
        one_hot = torch.full((tgt_vocab_size,), label_smoothing / (tgt_vocab_size - 2))
        one_hot[self.padding_idx] = 0
        super(LabelSmoothingLoss, self).__init__()
        self.register_buffer('one_hot', one_hot.unsqueeze(0))

    def forward(self, output, target):
        numel = target.ne(self.padding_idx).float().sum()
        truth = self.one_hot.repeat(target.size(0), 1)
        truth.scatter_(1, target.unsqueeze(1), 1 - self.label_smoothing)
        truth.masked_fill_((target == self.padding_idx).unsqueeze(1), 0)
        loss = func.kl_div(output, truth, reduction="sum")
        return loss / numel

    def forward_approx(self, output, target):
        non_pad_mask = target.ne(self.padding_idx)
        nll_loss = -output.gather(dim=-1, index=target.view(-1, 1))[non_pad_mask].sum()
        smooth_loss = -output.sum(dim=-1, keepdim=True)[non_pad_mask].sum()
        eps_i = self.label_smoothing / self.vocab
        loss = (1. - self.label_smoothing) * nll_loss + eps_i * smooth_loss
        return loss / non_pad_mask.float().sum()
