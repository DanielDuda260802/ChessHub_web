import torch
import torch.nn as nn
import torch.nn.functional as F

class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        residual = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        out = self.relu(out)
        return out

class ChessModel(nn.Module):
    def __init__(self, in_channels=112, num_policy_classes=4672, num_blocks=20, dropout_prob=0.3):
        super().__init__()

        self.initial_conv = nn.Conv2d(in_channels, 128, kernel_size=3, padding=1)
        self.initial_bn = nn.BatchNorm2d(128)
        self.relu = nn.ReLU()

        self.res_blocks = nn.Sequential(*[ResBlock(128) for _ in range(num_blocks)])

        self.flatten = nn.Flatten()
        self.feature_dim = 8 * 8 * 128
        self.dropout = nn.Dropout(p=dropout_prob)

        self.fc = nn.Linear(self.feature_dim + 7, 256)
        self.policy_head = nn.Linear(256, num_policy_classes)
        self.value_head = nn.Linear(256, 1)

    def forward(self, board_tensor, meta):
        x = self.relu(self.initial_bn(self.initial_conv(board_tensor)))
        x = self.res_blocks(x)
        x = self.flatten(x)
        x = torch.cat([x, meta], dim=1)
        x = self.relu(self.fc(x))
        x = self.dropout(x)

        policy_logits = self.policy_head(x)
        value = self.value_head(x).squeeze(-1)
        return policy_logits, value
