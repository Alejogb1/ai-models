# =========================
# 1. Imports
# =========================
import torch
import torch.nn as nn
import torch.optim as optim

from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader

import os

# =========================
# 2. Device (GPU)
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# =========================
# 3. Transforms
# =========================
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std =[0.229, 0.224, 0.225]
    )
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std =[0.229, 0.224, 0.225]
    )
])

# =========================
# 4. Dataset (folder structure)
# =========================
# dataset/
#   train/
#     class1/
#     class2/
#   val/
#     class1/
#     class2/

data_dir = "./content"

train_dataset = datasets.ImageFolder(
    os.path.join(data_dir, "train"),
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    os.path.join(data_dir, "validation"),
    transform=val_transform
)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader   = DataLoader(val_dataset, batch_size=32, shuffle=False)

num_classes = len(train_dataset.classes)
print("Classes:", train_dataset.classes)

# =========================
# 5. Model (AlexNet)
# =========================
model = models.alexnet(weights="IMAGENET1K_V1")

# Replace final layer
model.classifier[6] = nn.Linear(4096, num_classes)

model = model.to(device)

# =========================
# 6. Loss + Optimizer
# =========================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-4)

# =========================
# 7. Training Loop
# =========================
epochs = 10

for epoch in range(epochs):
    model.train()
    running_loss = 0.0

    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    print(f"Epoch [{epoch+1}/{epochs}] Loss: {running_loss:.4f}")

    # =========================
    # 8. Validation
    # =========================
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            _, predicted = torch.max(outputs, 1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    acc = 100 * correct / total
    print(f"Validation Accuracy: {acc:.2f}%")

# =========================
# 9. Save Model
# =========================
torch.save(model.state_dict(), "alexnet_model.pth")

# =========================
# 10. Load Model (later)
# =========================
# model.load_state_dict(torch.load("alexnet_model.pth"))
# model.eval()

# =========================
# 11. Inference on single image
# =========================
from PIL import Image

def predict(image_path):
    model.eval()

    img = Image.open(image_path).convert("RGB")
    x = val_transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(x)
        probs = torch.nn.functional.softmax(outputs[0], dim=0)

    top_prob, top_class = torch.max(probs, 0)

    return train_dataset.classes[top_class], top_prob.item()


# Example
# print(predict("test.jpg"))