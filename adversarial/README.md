# Adversarial Image Generation

Reproducing the Nguyen et al. phenomenon: Generating images that look like noise to humans but are classified by neural networks with >99% confidence.

## Overview

This experiment explores the fundamental differences between human and neural network perception. We generate adversarial images that:
- Look like random noise/static to human observers
- Are classified as specific objects (ships, bikes) by CNNs with high confidence
- Reveal insights into what features neural networks actually use

## Results

![Adversarial Ship Example](results/adversarial_ship.jpg)

**Key Finding**: Model classifies pure noise as "ship" with 99.8% confidence.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Prepare data (CIFAR-10: ships vs bikes)
python main.py

# Train model
python model.py

# Generate adversarial examples
python adversarial_generator.py
```

## Experiment Details

- **Dataset**: CIFAR-10 (ships vs bicycles)
- **Model**: AlexNet (pre-trained on ImageNet, fine-tuned)
- **Method**: Gradient-based optimization on random noise
- **Iterations**: 500 optimization steps
- **Final Accuracy**: 95% on validation set

## How It Works

1. Start with pure random noise
2. Optimize noise to maximize target class probability
3. Model confidence increases from ~50% to >99%
4. Result: Unrecognizable image with high classification confidence

## Files

- `model.py` - Model training code
- `adversarial_generator.py` - Adversarial image generation
- `main.py` - Data preparation
- `test_model.py` - Model inference testing

## Reference

Based on: Nguyen et al. - "Deep Neural Networks are Easily Fooled"

## Requirements

- Python 3.8+
- CUDA-capable GPU (recommended)
- PyTorch 2.0+
