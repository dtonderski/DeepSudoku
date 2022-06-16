import torch
from torch import nn


class ConvBlock(nn.Module):
    def __init__(self):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels=1, out_channels=64,
                              kernel_size=(3, 3), stride=(1, 1), padding=1)
        self.bn = nn.BatchNorm2d(64)

    def forward(self, s):
        return torch.relu(self.bn(self.conv(s)))


class ResBlock(nn.Module):
    def __init__(self):
        super(ResBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=64, out_channels=64,
                               kernel_size=(3, 3), stride=(1, 1),
                               padding=1)

        self.bn1 = nn.BatchNorm2d(64)
        self.conv2 = nn.Conv2d(in_channels=64, out_channels=64,
                               kernel_size=(3, 3), stride=(1, 1),
                               padding=1)
        self.bn2 = nn.BatchNorm2d(64)

    def forward(self, x):
        skip = x
        x = self.bn1(self.conv1(x))
        x = self.bn2(self.conv2(x))
        x += skip
        return torch.relu(x)


class ValueBlock(nn.Module):
    def __init__(self):
        super(ValueBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels=64, out_channels=3,
                              kernel_size=1)
        self.bn = nn.BatchNorm2d(3)
        self.fc1 = nn.Linear(3 * 9 * 9, 32)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x):
        x = torch.relu(self.bn(self.conv(x)))
        x = x.view(-1, 3 * 9 * 9)
        x = torch.relu(self.fc1(x))
        return torch.tanh(self.fc2(x))


class PolicyBlock(nn.Module):
    def __init__(self):
        super(PolicyBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels=64, out_channels=9,
                              kernel_size=(3, 3), stride=(1, 1), padding = 1)

    def forward(self, x):
        return self.conv(x)


class Network(nn.Module):
    def __init__(self):
        super(Network, self).__init__()
        self.convBlock = ConvBlock()
        self.resBlockList = []
        for i in range(5):
            setattr(self, f"res_{i}", ResBlock())
        self.valueBlock = ValueBlock()
        self.policyBlock = PolicyBlock()

    def forward(self, x: torch.Tensor):
        """
        
        :param x: (batch_size,1,9,9) tensor representing the sudokus
        :return v: (batch_size, 1) tensor representing the predicted value.
                   Note that these are logits.
        :return p: (batch_size,9,9,9) tensor representing unnormalized scores,
                   converted to a probability distribution of moves for each
                   cell through a softmax.
        """
        x = self.convBlock(x)
        for i in range(5):
            x = getattr(self, f"res_{i}")(x)
        p = self.policyBlock(x)
        v = self.valueBlock(x)
        return v, p