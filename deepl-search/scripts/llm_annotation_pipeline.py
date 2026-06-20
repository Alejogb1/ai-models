"""LLM Annotation Pipeline.

Generates intent labels for N unlabeled queries using an LLM.
Output: deepl-search/data/llm_labeled_queries.jsonl

Usage:
    set LLM_API_BASE=https://api.groq.com/openai/v1
    set LLM_API_KEY=gsk_your_key_here
    set LLM_MODEL=llama3-70b-8192
    python scripts/llm_annotation_pipeline.py

Output: deepl-search/data/llm_labeled_queries.jsonl
"""

import os
import json
import time
import csv
from typing import Optional


L1_CATEGORIES = [
    "Arts & Entertainment", "Business & Finance", "Computers & Technology",
    "Education & Reference", "Food & Dining", "Health & Fitness",
    "Shopping & Commerce", "Travel & Local",
]

L1_DESCRIPTIONS = {
    "Arts & Entertainment": "Movies, music, TV, celebrities, art, literature, entertainment events.",
    "Business & Finance": "Companies, investing, banking, insurance, real estate, financial services.",
    "Computers & Technology": "Software, hardware, programming, networking, cybersecurity, AI, mobile, cloud computing.",
    "Education & Reference": "Schools, academic subjects, research, dictionaries, encyclopedias, learning.",
    "Food & Dining": "Restaurants, recipes, cooking tips, beverages, cuisine types, dining out, food science.",
    "Health & Fitness": "Exercise, mental health, medical conditions, medications, nutrition, wellness, senior health.",
    "Shopping & Commerce": "Buying products, clothing, electronics, home goods, beauty, sports gear, books, groceries.",
    "Travel & Local": "Destinations, hotels, flights, public transit, maps, local services, events, weather.",
}


def load_queries(filepath: str, max_queries: int = None):
    queries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 2:
                queries.append({"id": row[0], "text": row[1]})
            if max_queries and len(queries) >= max_queries:
                break
    return queries


def build_prompt(query_text: str) -> str:
    categories_str = "\n".join(
        f"{i+1}. {c}: {L1_DESCRIPTIONS[c]}" for i, c in enumerate(L1_CATEGORIES)
    )
    return f"""Classify this search query into ONE of the following categories.

{categories_str}

Respond with only a JSON object:
{{"l1_category": "<category_name>", "confidence": "<high|medium|low>", "is_commercial": true/false}}

Query: {query_text}"""


def parse_response(raw: str) -> Optional[dict]:
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(l for l in lines if not l.startswith("```"))
        obj = json.loads(cleaned)
        if obj.get("l1_category") in L1_CATEGORIES:
            return obj
    except (json.JSONDecodeError, AttributeError):
        for cat in L1_CATEGORIES:
            if cat.lower() in raw.lower():
                return {"l1_category": cat, "confidence": "medium", "is_commercial": False}
    return None


def annotate_queries(queries, output_path: str, checkpoint: int = 50):
    api_base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    from openai import OpenAI
    client = OpenAI(base_url=api_base, api_key=api_key)

    max_retries = 3
    results = []
    errors = []

    for i, q in enumerate(queries):
        prompt = build_prompt(q["text"])
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=80,
                )
                raw = resp.choices[0].message.content.strip()
                parsed = parse_response(raw)
                if parsed:
                    results.append({
                        "query_id": q["id"],
                        "query_text": q["text"],
                        **parsed,
                    })
                else:
                    errors.append({"query_id": q["id"], "raw": raw, "error": "parse_failed"})
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    errors.append({"query_id": q["id"], "error": str(e)})

        if (i + 1) % checkpoint == 0:
            _save(results, errors, len(queries), model, output_path)
            print(f"  Checkpoint: {i+1}/{len(queries)} done, {len(results)} labeled, {len(errors)} errors")

    _save(results, errors, len(queries), model, output_path)
    print(f"\nDone: {len(results)} labeled, {len(errors)} errors")
    return results


def _save(results, errors, total, model, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    meta_path = output_path.replace(".jsonl", "_meta.json")
    with open(meta_path, 'w') as f:
        json.dump({"total": total, "completed": len(results), "errors": len(errors),
                    "model": model}, f, indent=2)


if __name__ == "__main__":
    queries_path = os.environ.get(
        "QUERIES_PATH",
        os.path.expanduser(r"~\.ir_datasets\msmarco-passage\train\queries.tsv")
    )
    output_path = os.environ.get(
        "OUTPUT_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "data", "llm_labeled_queries.jsonl")
    )
    n_queries = int(os.environ.get("N_LABEL", "1000"))

    print(f"Loading up to {n_queries} queries...")
    all_q = load_queries(queries_path, max_queries=n_queries)
    print(f"Loaded {len(all_q)} queries")

    print(f"Annotating with model: {os.environ.get('LLM_MODEL', 'default')}")
    annotate_queries(all_q, output_path)
    print(f"Output: {output_path}")
