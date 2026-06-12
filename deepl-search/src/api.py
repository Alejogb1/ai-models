"""
Deepl Search API — Intent Classification Service
=================================================
FastAPI endpoints for query-to-intent mapping.

Endpoints:
  POST /classify         — Classify a query into intent classes
  POST /classify/batch   — Batch classify multiple queries
  GET  /taxonomy         — Get the full taxonomy skeleton
  GET  /taxonomy/advertiser — Get advertiser-pruned taxonomy
  GET  /health           — Health check
"""

from __future__ import annotations

import os
import time
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from taxonomy import build_skeleton, count_leaves, count_by_level, to_skos_json, get_all_leaves
from classifier import EmbeddingClassifier, LLMClassifier
from intent_vector import IntentVectorEncoder
from ads_mapping import AdvertiserMapper

app = FastAPI(
    title="Deepl Search Intent API",
    version="0.1.0",
    description="Query-to-intent classification with hierarchical taxonomy",
)

# Initialize on startup
_clf: Optional[EmbeddingClassifier] = None
_llm: Optional[LLMClassifier] = None
_encoder: Optional[IntentVectorEncoder] = None
_ads: Optional[AdvertiserMapper] = None
_root = build_skeleton()


@app.on_event("startup")
def startup():
    global _clf, _encoder, _ads
    _clf = EmbeddingClassifier()
    _encoder = IntentVectorEncoder()
    _ads = AdvertiserMapper()


# --- Request/Response Models ---

class ClassifyRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of intent classes to return")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence score")
    method: str = Field(default="embedding", pattern="^(embedding|llm)$", description="Classifier backend")


class ClassifyResponse(BaseModel):
    query: str
    labels: list[dict]
    vector_preview: list[float]  # first 10 dims + length
    vector_dim: int
    method: str
    latency_ms: float


class BatchClassifyRequest(BaseModel):
    queries: list[str] = Field(..., min_length=1, max_length=100, description="Batch of queries")
    top_k: int = Field(default=5, ge=1, le=50)
    method: str = Field(default="embedding", pattern="^(embedding|llm)$")


class BatchClassifyResponse(BaseModel):
    results: list[ClassifyResponse]
    total_latency_ms: float


class TaxonomyResponse(BaseModel):
    depth: int
    l1_count: int
    l2_count: int
    l3_count: int
    l4_count: int
    total_leaves: int
    branching: dict
    skos: Optional[dict] = None


class AdvertiserResponse(BaseModel):
    total_intent_classes: int
    advertiser_classes: int
    pruning_ratio: float
    commercial_pct: float
    top_classes: list[dict]


# --- Endpoints ---

@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    if _clf is None:
        raise HTTPException(503, "Classifier not initialized")

    if req.method == "embedding":
        result = _clf.classify(req.query, top_k=req.top_k, threshold=req.threshold)
    else:
        if _llm is None:
            raise HTTPException(501, "LLM classifier requires OpenAI API key")
        result = _llm.classify(req.query, top_k=req.top_k)

    vec = _encoder.encode(result)
    vec_preview = vec[:10].tolist() + [float(len(vec))]

    return ClassifyResponse(
        query=result.query,
        labels=result.labels,
        vector_preview=vec_preview,
        vector_dim=_encoder.dim,
        method=result.method,
        latency_ms=result.latency_ms,
    )


@app.post("/classify/batch", response_model=BatchClassifyResponse)
def classify_batch(req: BatchClassifyRequest):
    if _clf is None:
        raise HTTPException(503, "Classifier not initialized")

    start = time.time()
    results = []
    for query in req.queries:
        result = _clf.classify(query, top_k=req.top_k)
        vec = _encoder.encode(result)
        vec_preview = vec[:10].tolist() + [float(len(vec))]
        results.append(ClassifyResponse(
            query=result.query,
            labels=result.labels,
            vector_preview=vec_preview,
            vector_dim=_encoder.dim,
            method=result.method,
            latency_ms=result.latency_ms,
        ))

    return BatchClassifyResponse(
        results=results,
        total_latency_ms=round((time.time() - start) * 1000, 1),
    )


@app.get("/taxonomy", response_model=TaxonomyResponse)
def get_taxonomy(include_skos: bool = False):
    l1 = count_by_level(_root, 1)
    l2 = count_by_level(_root, 2)
    l3 = count_by_level(_root, 3)
    leaves = count_leaves(_root)

    skos = to_skos_json(_root) if include_skos else None

    return TaxonomyResponse(
        depth=4,
        l1_count=l1,
        l2_count=l2,
        l3_count=l3,
        l4_count=leaves,
        total_leaves=leaves,
        branching={
            "L1->L2": round(l2 / l1, 2),
            "L2->L3": round(l3 / l2, 2),
            "L3->L4": round(leaves / l3, 2),
        },
        skos=skos,
    )


@app.get("/taxonomy/advertiser", response_model=AdvertiserResponse)
def get_advertiser_taxonomy():
    if _ads is None:
        raise HTTPException(503, "Advertiser mapper not initialized")
    data = _ads.get_advertiser_taxonomy()
    return AdvertiserResponse(**data)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "taxonomy": {
            "depth": 4,
            "leaves": count_leaves(_root),
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
