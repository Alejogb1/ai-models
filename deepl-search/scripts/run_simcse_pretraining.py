"""SimCSE Contrastive Pre-training on Queries.

Trains all-MiniLM-L6-v2 with SimCSE unsupervised objective on MS MARCO queries.
Positive pairs: same query with different dropout masks.
Tests if contrastive pre-training improves downstream intent retrieval.

Rewrite: uses transformers + torch directly (sentence_transformers import is broken).

Usage:
    python scripts/run_simcse_pretraining.py

Output: deepl-search/models/simcse_query_encoder/
         deepl-search/experiments/contrastive_pretraining_results.json
"""

import os
import json
import csv
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel


def load_queries(filepath: str, max_queries: int = 100000):
    queries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 2:
                queries.append(row[1])
            if max_queries and len(queries) >= max_queries:
                break
    return queries


def load_session_pairs(filepath: str):
    pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            session = json.loads(line)
            qs = session.get("queries", [])
            for i in range(len(qs) - 1):
                pairs.append((qs[i], qs[i + 1]))
    return pairs


class TransformerEncoder(nn.Module):
    """Wrapper around a HF transformer model that returns mean-pooled embeddings."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__()
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.hidden_dim = self.model.config.hidden_size

    def forward(self, input_ids, attention_mask, **kwargs):
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
        # Mean pooling
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1)
        sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
        return sum_embeddings / sum_mask

    def encode(self, texts, device=None, batch_size=64, show_progress_bar=False):
        if device is None:
            device = next(self.parameters()).device
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            inputs = self.tokenizer(batch, padding=True, truncation=True,
                                     max_length=128, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                emb = self.forward(**inputs)
            all_embeddings.append(emb.cpu().numpy())
        return np.concatenate(all_embeddings, axis=0)


def simcse_contrastive_loss(z1, z2, temperature=0.05):
    """Unsupervised SimCSE contrastive loss.
    
    z1, z2: (batch_size, hidden_dim) — two dropout views of the same batch.
    Pulls together (z1[i], z2[i]), pushes apart all other pairs.
    """
    batch_size = z1.shape[0]
    z = torch.cat([z1, z2], dim=0)
    z = F.normalize(z, dim=1)
    sim = torch.mm(z, z.t()) / temperature

    # Mask out self-comparisons
    mask = torch.eye(2 * batch_size, device=z.device, dtype=torch.bool)
    sim = sim.masked_fill(mask, -1e9)

    # Labels: examples i and i+batch_size are the positive pair
    labels = torch.cat([torch.arange(batch_size, 2 * batch_size, device=z.device),
                        torch.arange(0, batch_size, device=z.device)], dim=0)
    return F.cross_entropy(sim, labels)


def evaluate_retrieval(model, session_pairs, n_sample=200, device="cpu"):
    if len(session_pairs) == 0:
        return {}
    pairs = session_pairs[:n_sample]
    emb1 = model.encode([p[0] for p in pairs], device=device, show_progress_bar=False)
    emb2 = model.encode([p[1] for p in pairs], device=device, show_progress_bar=False)
    emb1 = emb1 / np.linalg.norm(emb1, axis=1, keepdims=True)
    emb2 = emb2 / np.linalg.norm(emb2, axis=1, keepdims=True)
    similarities = (emb1 * emb2).sum(axis=1)
    return {
        "mean_similarity": float(similarities.mean()),
        "std_similarity": float(similarities.std()),
        "pct_above_0_5": float((similarities > 0.5).mean()),
        "pct_above_0_3": float((similarities > 0.3).mean()),
    }


def run():
    queries_path = os.environ.get(
        "QUERIES_PATH",
        os.path.expanduser(r"~\.ir_datasets\msmarco-passage\train\queries.tsv")
    )
    sessions_path = os.environ.get(
        "SESSIONS_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "data", "session_dataset.jsonl")
    )
    output_model_path = os.environ.get(
        "OUTPUT_MODEL_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "models", "simcse_query_encoder")
    )
    output_results_path = os.environ.get(
        "OUTPUT_RESULTS_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "experiments", "contrastive_pretraining_results.json")
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    print("Loading queries...")
    queries = load_queries(queries_path, max_queries=50000)
    print(f"Loaded {len(queries)} queries")

    print("Loading session pairs...")
    session_pairs = load_session_pairs(sessions_path)
    print(f"Loaded {len(session_pairs)} session pairs")

    print("Loading base model: all-MiniLM-L6-v2...")
    model = TransformerEncoder("sentence-transformers/all-MiniLM-L6-v2")
    model.to(device)
    model.train()

    # Evaluate BEFORE pre-training on session pairs
    print("\nEvaluating BEFORE contrastive pre-training...")
    model.eval()
    before = evaluate_retrieval(model, session_pairs, device=device)
    print(f"  mean_sim={before.get('mean_similarity', 0):.4f}, >0.5={before.get('pct_above_0_5', 0):.1%}")

    # Prepare SimCSE training data (first 20K queries)
    train_texts = queries[:20000]
    print(f"Preparing {len(train_texts)} training examples...")

    # Training
    print("Training with SimCSE contrastive loss (2 epochs)...")
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    batch_size = 64
    n_batches = len(train_texts) // batch_size
    temperature = 0.5

    for epoch in range(2):
        epoch_loss = 0.0
        np.random.shuffle(train_texts)
        for i in range(0, len(train_texts), batch_size):
            batch = train_texts[i:i+batch_size]
            if len(batch) < 2:
                continue

            # Tokenize once, feed twice with different dropout
            inputs = model.tokenizer(batch, padding=True, truncation=True,
                                     max_length=128, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # First forward pass (current dropout state)
            z1 = model.forward(**inputs)

            # Second forward pass — model is in train() mode so dropout is active,
            # and each forward() call naturally produces a different dropout mask.
            z2 = model.forward(**inputs)

            loss = simcse_contrastive_loss(z1, z2, temperature=temperature)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            epoch_loss += loss.item()
            if (i // batch_size) % 50 == 0:
                print(f"  Epoch {epoch+1}, batch {i//batch_size}/{n_batches}, loss={loss.item():.4f}", flush=True)

        avg_loss = epoch_loss / max(n_batches, 1)
        print(f"Epoch {epoch+1} complete. Avg loss: {avg_loss:.4f}", flush=True)

    # Save model
    os.makedirs(output_model_path, exist_ok=True)
    model.model.save_pretrained(output_model_path)
    model.tokenizer.save_pretrained(output_model_path)
    print(f"Model saved to {output_model_path}")

    # Evaluate AFTER pre-training
    print("\nEvaluating AFTER contrastive pre-training...")
    model.eval()
    after = evaluate_retrieval(model, session_pairs, device=device)
    print(f"  mean_sim={after.get('mean_similarity', 0):.4f}, >0.5={after.get('pct_above_0_5', 0):.1%}")

    results = {
        "n_queries_trained": len(train_texts),
        "n_session_pairs_eval": min(len(session_pairs), 200),
        "vanilla_all_minilm": before,
        "simcse_trained": after,
        "delta": {
            "mean_similarity": after.get("mean_similarity", 0) - before.get("mean_similarity", 0),
            "std_similarity": after.get("std_similarity", 0) - before.get("std_similarity", 0),
        }
    }

    os.makedirs(os.path.dirname(output_results_path), exist_ok=True)
    with open(output_results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n=== Results ===")
    print(f"Vanilla all-MiniLM:  mean_sim={before.get('mean_similarity', 0):.4f}, >0.5={before.get('pct_above_0_5', 0):.1%}")
    print(f"SimCSE (20K queries): mean_sim={after.get('mean_similarity', 0):.4f}, >0.5={after.get('pct_above_0_5', 0):.1%}")
    print(f"Delta: mean_sim={results['delta']['mean_similarity']:+.4f}")
    print(f"\nResults saved to {output_results_path}")


if __name__ == "__main__":
    run()
