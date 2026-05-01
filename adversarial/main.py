import os
import numpy as np
from tqdm import tqdm
from PIL import Image
from tensorflow.keras.datasets import cifar10

# Load CIFAR-10
(train_images, train_labels), (test_images, test_labels) = cifar10.load_data()

# Combine train + test
images = np.concatenate([train_images, test_images], axis=0)
labels = np.concatenate([train_labels, test_labels], axis=0).flatten()

# CIFAR-10 class IDs
SHIP_CLASS = 8
BICYCLE_CLASS = 1

# Output folders
os.makedirs("./content/train/ships", exist_ok=True)
os.makedirs("./content/train/bikes", exist_ok=True)
os.makedirs("./content/validation/ships", exist_ok=True)
os.makedirs("./content/validation/bikes", exist_ok=True)

def save_class_images(images, labels, class_id, train_dir, val_dir, n_train=100, n_val=50):
    class_indices = np.where(labels == class_id)[0]

    if len(class_indices) < n_train + n_val:
        raise ValueError(f"Not enough images for class {class_id}")

    np.random.shuffle(class_indices)

    train_indices = class_indices[:n_train]
    val_indices = class_indices[n_train:n_train + n_val]

    # Save training images
    for i, idx in enumerate(tqdm(train_indices, desc=f"Train class {class_id}")):
        img = images[idx]
        save_path = os.path.join(train_dir, f"img{i}.jpg")
        Image.fromarray(img).save(save_path)

    # Save validation images
    for i, idx in enumerate(tqdm(val_indices, desc=f"Val class {class_id}")):
        img = images[idx]
        save_path = os.path.join(val_dir, f"img{i}.jpg")
        Image.fromarray(img).save(save_path)

# Save ships
save_class_images(
    images, labels,
    SHIP_CLASS,
    "./content/train/ships",
    "./content/validation/ships"
)

# Save bicycles
save_class_images(
    images, labels,
    BICYCLE_CLASS,
    "./content/train/bikes",
    "./content/validation/bikes"
)