import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt 
from model import model, device, val_transform, predict
from torchvision import transforms

def generate_adversarial_noise(target_class: int, iterations=500, lr = 0.05):
    """
    Generate adversarial noise for a given target class.
    
    Args:
        target_class: The class to generate adversarial noise for
        epsilon: The magnitude of the perturbation
    
    Returns:
        adversarial_noise: The generated adversarial noise
    """
    # CORRECT - create tensor first, then scale it properly
    noise = torch.randn(1, 3, 224, 224, device=device)
    noise = noise * 0.1  # Scale after creation
    noise.requires_grad_(True)  # Set requires_grad after scaling
    optimizer = torch.optim.Adam([noise], lr=lr)

    # create normal loop

    for i in range(iterations):
        optimizer.zero_grad()
        

        outputs = model(noise)
        loss = -outputs[0, target_class]

        loss.backward()

        optimizer.step()

        with torch.no_grad():
            noise.clamp_(0, 1)
        
        if i % 100 == 0:
            with torch.no_grad():
                probs = torch.softmax(outputs, dim=1)
                confidence = probs[0, target_class].item()
                print(f"Iteration {i}: Loss = {loss.item():.4f}, Confidence = {confidence:.4f}")
        
    return noise
        
if __name__ == "__main__":
    model.eval()

    adv_ship = generate_adversarial_noise(target_class=0, iterations=500, lr=0.01)

    to_pil = transforms.ToPILImage()
    img = to_pil(adv_ship[0].cpu())
    img.save("adversarial_ship.png")
    print("adv_ship saved")

    result = predict("adversarial_ship.png")
    print(f"pred: {result}")