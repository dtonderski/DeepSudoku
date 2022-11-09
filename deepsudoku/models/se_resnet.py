import torch
from torch import nn
from torch.nn import functional
from deepsudoku.utils.network_utils import to_categorical


class ConvBlock(nn.Module):
    def __init__(self, filters):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels=9, out_channels=filters,
                              kernel_size=3, padding=1)
        self.bn = nn.BatchNorm2d(filters)

    def forward(self, x):
        return torch.relu(self.bn(self.conv(x)))


class SqueezeExcitation(nn.Module):
    def __init__(self, filters, se_channels):
        super().__init__()
        self.filters = filters
        self.squeeze = nn.AdaptiveAvgPool2d(output_size=1)
        # Conv2d because our channels are in second dimension so Linear
        # can't deal with it. Could do flattening and stuff
        self.fc1 = nn.Conv2d(filters, se_channels, kernel_size=1)
        self.fc2 = nn.Conv2d(se_channels, 2 * filters, kernel_size=1)

    def forward(self, x):
        squeezed = self.squeeze(x)
        excited = self.fc1(squeezed)
        excited = functional.relu(excited)
        excited = self.fc2(excited)

        weight, bias = torch.split(excited, self.filters, dim=1)
        weight = torch.sigmoid(weight)
        return x * weight + bias


class SeResBlock(nn.Module):
    def __init__(self, filters, se_channels):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=filters, out_channels=filters,
                               kernel_size=3, padding=1)

        self.bn1 = nn.BatchNorm2d(filters)
        self.conv2 = nn.Conv2d(in_channels=filters, out_channels=filters,
                               kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(filters)
        self.se = SqueezeExcitation(filters, se_channels)

    def forward(self, x):
        skip = x
        x = torch.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        x = self.se(x)
        x += skip
        return torch.relu(x)


class PolicyBlock(nn.Module):
    def __init__(self, filters):
        super(PolicyBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=filters, out_channels=filters,
                               kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(filters)
        self.conv2 = nn.Conv2d(in_channels=filters, out_channels=9,
                               kernel_size=3, padding=1)

    def forward(self, x):
        x = torch.relu(self.bn1(self.conv1(x)))
        return self.conv2(x)


class ValueBlock(nn.Module):
    def __init__(self, filters, value_channels):
        super(ValueBlock, self).__init__()
        self.value_channels = value_channels
        self.conv = nn.Conv2d(in_channels=filters,
                              out_channels=value_channels,
                              kernel_size=3, padding=1)
        self.bn = nn.BatchNorm2d(value_channels)
        self.fc1 = nn.Linear(value_channels * 9 * 9, 128)

        self.fc2 = nn.Linear(128, 1)

    def forward(self, x):
        x = torch.relu(self.bn(self.conv(x)))
        x = x.view(-1, self.value_channels * 9 * 9)
        x = torch.relu(self.fc1(x))
        return self.fc2(x)


class SeResNet(nn.Module):
    def __init__(self, blocks, filters, se_channels, value_channels=32):
        super().__init__()
        self.blocks = blocks
        self.convBlock = ConvBlock(filters)

        for i in range(self.blocks):
            setattr(self, f"block_{i}", SeResBlock(filters, se_channels))
        self.valueBlock = ValueBlock(filters, value_channels=value_channels)
        self.policyBlock = PolicyBlock(filters)

    def forward(self, x: torch.Tensor):
        """

        :param x: (batch_size,9,9,9) tensor one-hot encoded tensor OR
                  (batch_size,1,9,9) tensor where blanks represent 0s
        :return v: (batch_size, 1) tensor representing the predicted value of
                   the sudoku, the unnormalized 'probability' that the sudoku
                   is valid. Note that these are unnormalized logits.
        :return p: (batch_size,9,9,9) tensor representing unnormalized scores,
                   converted to a probability distribution of moves for each
                   cell through a softmax.
        """
        if x.shape[1] == 1:
            # Must one-hot encode!
            x = to_categorical(x)

        x = self.convBlock(x)
        for i in range(self.blocks):
            x = getattr(self, f"block_{i}")(x)
        p = self.policyBlock(x)
        v = self.valueBlock(x)
        return p, v


def main():
    x = torch.zeros((25, 1, 9, 9))
    print(x.shape)
    model = SeResNet(10, 128, 32)
    x = model(x)
    print(x[0].shape, x[1].shape)


if __name__ == '__main__':
    main()
