# Example from https://pytorch.org/tutorials/beginner/basics/
#   quickstart_tutorial.html
import os
from torch import nn
weights_file = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), 'model_weights.pth'))
data_root = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'Input', 'data'))
input_file = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'Input', 'input.png'))
output_file = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'Output', 'output.txt'))


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 10)
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits


def input_transform(x):
    from torchvision.transforms import ToTensor
    from PIL import Image
    return (ToTensor()(Image.fromarray(x)), )


def output_transform(x):
    out = x.detach().numpy()
    out = out.astype({'names': ['f0'],
                      'formats': [out.dtype]})
    out = out.flatten()
    return out


def load_model():
    import torch
    import numpy as np
    from torchvision import datasets
    from torchvision.transforms import ToTensor, functional
    
    test_data = datasets.FashionMNIST(
        root=data_root,
        train=False,
        download=True,
        transform=ToTensor()
    )
    
    model = NeuralNetwork()
    model.load_state_dict(torch.load(weights_file))
    model.eval()

    mock = test_data[0][0]
    im = functional.to_pil_image(mock)
    im.save(input_file)
    out = model(mock)
    arr = out.detach().numpy()
    np.savetxt(output_file, arr)


def train_model():
    import torch
    from torch.utils.data import DataLoader
    from torchvision import datasets
    from torchvision.transforms import ToTensor
    from torch import nn
    training_data = datasets.FashionMNIST(
        root=data_root,
        train=True,
        download=True,
        transform=ToTensor()
    )
    test_data = datasets.FashionMNIST(
        root=data_root,
        train=False,
        download=True,
        transform=ToTensor()
    )
    train_dataloader = DataLoader(
        training_data, batch_size=64, shuffle=True)
    test_dataloader = DataLoader(
        test_data, batch_size=64, shuffle=True)

    model = NeuralNetwork()

    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

    def train(dataloader, model, loss_fn, optimizer):
        size = len(dataloader.dataset)
        model.train()
        for batch, (X, y) in enumerate(dataloader):

            # Compute prediction error
            pred = model(X)
            loss = loss_fn(pred, y)

            # Backpropagation
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            if batch % 100 == 0:
                loss, current = loss.item(), (batch + 1) * len(X)
                print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

    def test(dataloader, model, loss_fn):
        size = len(dataloader.dataset)
        num_batches = len(dataloader)
        model.eval()
        test_loss, correct = 0, 0
        with torch.no_grad():
            for X, y in dataloader:
                pred = model(X)
                test_loss += loss_fn(pred, y).item()
                correct += (
                    pred.argmax(1) == y).type(torch.float).sum().item()
        test_loss /= num_batches
        correct /= size
        print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, "
              f"Avg loss: {test_loss:>8f} \n")

    epochs = 5
    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train(train_dataloader, model, loss_fn, optimizer)
        test(test_dataloader, model, loss_fn)
        print("Done!")

    torch.save(model.state_dict(), weights_file)
    test(test_dataloader, model, loss_fn)
