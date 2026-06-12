"""
Intent Classifier
=================
Two backends:
  1. Embedding-based (free, no API key) — sentence-BERT similarity to class centroids
  2. LLM-based (requires API key) — zero-shot classification via OpenAI-compatible API
Both return multi-label results with confidence scores at all 4 levels.
"""

from __future__ import annotations

import json
import time
from typing import Optional
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

from taxonomy import build_skeleton, get_all_leaves, get_nodes_at_level, TaxonomyNode


@dataclass
class IntentResult:
    query: str
    labels: list[dict]  # [{"id": "A1.B3.C2.D5", "name": "...", "level": 4, "score": 0.87}, ...]
    vector: list[float]  # 3,843-dim weighted intent vector
    method: str  # "embedding" | "llm"
    latency_ms: float


class EmbeddingClassifier:
    """Sentence-BERT embedding similarity baseline. No API key needed."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.root = build_skeleton()
        self.leaves = get_all_leaves(self.root)
        self.leaf_texts = [self._leaf_text(l) for l in self.leaves]
        self.leaf_embeddings = self.model.encode(self.leaf_texts, show_progress_bar=False, convert_to_numpy=True)
        self.leaf_embeddings = self.leaf_embeddings / np.linalg.norm(self.leaf_embeddings, axis=1, keepdims=True)
        self.dim = self.leaf_embeddings.shape[1]

    def _leaf_text(self, leaf: TaxonomyNode) -> str:
        """Construct a descriptive text for each leaf node using its path names."""
        return " > ".join(leaf.path_names())

    def classify(self, query: str, top_k: int = 10, threshold: float = 0.0) -> IntentResult:
        start = time.time()
        q_emb = self.model.encode([query], convert_to_numpy=True)
        q_emb = q_emb / np.linalg.norm(q_emb)
        scores = self.leaf_embeddings @ q_emb.T
        scores = scores.flatten()

        # Get top-K
        top_indices = np.argsort(scores)[::-1][:top_k]
        labels = []
        vector = np.zeros(len(self.leaves), dtype=np.float32)
        for i in top_indices:
            if scores[i] >= threshold:
                leaf = self.leaves[i]
                labels.append({
                    "id": leaf.id,
                    "name": leaf.name,
                    "level": leaf.level,
                    "score": float(round(scores[i], 4)),
                    "path": leaf.path(),
                    "path_names": leaf.path_names(),
                })
                vector[i] = float(scores[i])

        latency_ms = round((time.time() - start) * 1000, 1)
        return IntentResult(
            query=query,
            labels=labels,
            vector=vector.tolist(),
            method="embedding",
            latency_ms=latency_ms,
        )


class LLMClassifier:
    """Zero-shot LLM classification via OpenAI-compatible API.
    Requires OPENAI_API_KEY env var or api_key parameter.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.root = build_skeleton()
        self.l1_names = [n.name for n in self.root.children]

    def classify(self, query: str, top_k: int = 5) -> IntentResult:
        start = time.time()

        prompt = f"""You are Deepl Search's intent classifier. Given a search query, classify it into one or more intent categories from the taxonomy below.

Taxonomy (8 L1 categories):
{chr(10).join(f'{i+1}. {n}' for i, n in enumerate(self.l1_names))}

Rules:
1. Return the top {top_k} most specific intent paths (L4 level)
2. Each path: "L1 name > L2 name > L3 name > L4 name"
3. Include a confidence score (0.0-1.0) for each
4. Be specific — don't default to "Other"
5. If the query is ambiguous, return multiple plausible intents

Return ONLY valid JSON:
{{"intents": [{{"path": "Arts & Entertainment > Music > Rock > Classic Rock", "score": 0.95}}]}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": f"{prompt}\n\nQuery: {query}"}],
            temperature=0.1,
            max_tokens=500,
        )

        latency_ms = round((time.time() - start) * 1000, 1)
        text = response.choices[0].message.content.strip()

        # Parse JSON from response
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        labels = []
        if json_match:
            try:
                data = json.loads(json_match.group())
                for intent in data.get("intents", []):
                    labels.append({
                        "id": intent.get("path", ""),
                        "name": intent.get("path", "").split(" > ")[-1] if " > " in intent.get("path", "") else intent.get("path", ""),
                        "level": 4,
                        "score": intent.get("score", 0.5),
                        "path_names": intent.get("path", "").split(" > ") if " > " in intent.get("path", "") else [intent.get("path", "")],
                    })
            except json.JSONDecodeError:
                pass

        return IntentResult(
            query=query,
            labels=labels,
            vector=[],
            method=f"llm:{self.model}",
            latency_ms=latency_ms,
        )


if __name__ == "__main__":
    # Test embedding classifier
    clf = EmbeddingClassifier()
    queries = ["nike air max size 10", "how to fix a leaky faucet", "best pizza near me", "python tutorial for beginners"]
    for q in queries:
        result = clf.classify(q, top_k=3)
        print(f"\nQuery: {q}")
        print(f"Method: {result.method}, Latency: {result.latency_ms}ms")
        for label in result.labels[:3]:
            print(f"  {label['id']:20s} {label['name']:20s} score={label['score']:.4f}")
