"""B8 Baseline: LLM Zero-Shot Intent Classification.

Runs 500 MS MARCO queries through an LLM to classify into 8 L1 intent categories.
Provider-agnostic: configure via environment variables.

Usage:
    set LLM_API_BASE=https://api.groq.com/openai/v1
    set LLM_API_KEY=gsk_your_key_here
    set LLM_MODEL=llama3-70b-8192
    python scripts/run_b8_baseline.py

Output: deepl-search/experiments/b8_baseline_results.json
"""

import os
import json
import time
import csv
import random
from typing import List, Dict, Optional

L1_CATEGORIES = [
    "Arts & Entertainment",
    "Business & Finance",
    "Computers & Technology",
    "Education & Reference",
    "Food & Dining",
    "Health & Fitness",
    "Shopping & Commerce",
    "Travel & Local",
]

L1_DESCRIPTIONS = {
    "Arts & Entertainment": "Queries about movies, music, TV shows, celebrities, art, literature, and entertainment events.",
    "Business & Finance": "Queries about companies, investing, banking, insurance, real estate, and financial services.",
    "Computers & Technology": "Queries about software, hardware, programming, networking, cybersecurity, AI, mobile, and cloud computing.",
    "Education & Reference": "Queries about schools, academic subjects, research, dictionaries, encyclopedias, and learning.",
    "Food & Dining": "Queries about restaurants, recipes, cooking tips, beverages, cuisine types, dining out, and food science.",
    "Health & Fitness": "Queries about exercise, mental health, medical conditions, medications, nutrition, wellness, and senior health.",
    "Shopping & Commerce": "Queries about buying products, clothing, electronics, home goods, beauty, sports gear, books, and groceries.",
    "Travel & Local": "Queries about destinations, hotels, flights, public transit, maps, local services, events, and weather.",
}

CATEGORY_EXAMPLES = {
    "Arts & Entertainment": '"movie showtimes" "song lyrics" "celebrity news"',
    "Business & Finance": '"stock price" "mortgage rates" "credit score"',
    "Computers & Technology": '"python tutorial" "best laptop 2025" "cloud computing"',
    "Education & Reference": '"define photosynthesis" "civil war dates" "online courses"',
    "Food & Dining": '"chicken recipes" "best restaurants near me" "how to brew coffee"',
    "Health & Fitness": '"workout routine" "flu symptoms" "meditation for beginners"',
    "Shopping & Commerce": '"buy running shoes" "best laptop deals" "amazon returns"',
    "Travel & Local": '"hotels in paris" "flight deals" "weather forecast"',
}


def load_queries(filepath: str, max_queries: int = None) -> List[Dict]:
    queries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 2:
                queries.append({"id": row[0], "text": row[1]})
            if max_queries and len(queries) >= max_queries:
                break
    return queries


def sample_balanced(queries: List[Dict], total: int = 500) -> List[Dict]:
    by_length = sorted(queries, key=lambda q: len(q["text"]))
    n = len(by_length)
    head = by_length[:n // 10]
    mid = by_length[n // 10: n // 2]
    tail = by_length[n // 2:]

    n_head = total // 2
    n_mid = total // 3
    n_tail = total - n_head - n_mid

    sampled = (
        random.sample(head, min(n_head, len(head))) +
        random.sample(mid, min(n_mid, len(mid))) +
        random.sample(tail, min(n_tail, len(tail)))
    )
    random.shuffle(sampled)
    return sampled


def build_prompt(query_text: str) -> str:
    categories_str = "\n".join(
        f"{i+1}. {cat}: {L1_DESCRIPTIONS[cat]}"
        for i, cat in enumerate(L1_CATEGORIES)
    )
    examples_str = "\n".join(
        f"- {cat} (e.g., {CATEGORY_EXAMPLES[cat]})"
        for cat in L1_CATEGORIES
    )

    return f"""You are a search query intent classifier. Classify the following search query into exactly ONE of the {len(L1_CATEGORIES)} categories below.

CATEGORIES:
{categories_str}

EXAMPLES:
{examples_str}

Respond with ONLY the category name. No explanations, no prefixes, no punctuation — just the category name.

Query: {query_text}"""


def parse_response(response: str) -> Optional[str]:
    response = response.strip().strip('"').strip("'")
    for cat in L1_CATEGORIES:
        if cat.lower() in response.lower():
            return cat
    return None


def run_baseline(queries: List[Dict], output_path: str, checkpoint_interval: int = 50):
    api_base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    from openai import OpenAI
    client = OpenAI(base_url=api_base, api_key=api_key)

    max_retries = 3
    results = []
    errors = []

    for idx, q in enumerate(queries):
        prompt = build_prompt(q["text"])
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=20,
                )
                raw = resp.choices[0].message.content.strip()
                predicted = parse_response(raw)
                results.append({
                    "query_id": q["id"],
                    "query_text": q["text"],
                    "raw_response": raw,
                    "predicted_label": predicted,
                    "model": model,
                })
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    errors.append({"query_id": q["id"], "error": str(e)})

        if (idx + 1) % checkpoint_interval == 0:
            with open(output_path, 'w') as f:
                json.dump({"results": results, "errors": errors, "total": len(queries),
                           "completed": idx + 1, "model": model}, f, indent=2)
            print(f"  Checkpoint: {idx+1}/{len(queries)} completed, {len(errors)} errors")

    with open(output_path, 'w') as f:
        json.dump({"results": results, "errors": errors, "total": len(queries),
                   "completed": len(results), "model": model}, f, indent=2)
    print(f"\nDone. {len(results)}/{len(queries)} successful. Errors: {len(errors)}")
    return results


if __name__ == "__main__":
    queries_path = os.environ.get(
        "QUERIES_PATH",
        os.path.expanduser(r"~\.ir_datasets\msmarco-passage\train\queries.tsv")
    )
    output_path = os.environ.get(
        "OUTPUT_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "experiments", "b8_baseline_results.json")
    )

    print("Loading queries...")
    all_queries = load_queries(queries_path, max_queries=None)

    print(f"Total queries loaded: {len(all_queries):,}")
    print("Sampling 500 balanced queries...")
    sampled = sample_balanced(all_queries, total=500)

    _stats = {
        "head": len([q for q in sampled if len(q["text"]) < 30]),
        "mid": len([q for q in sampled if 30 <= len(q["text"]) < 60]),
        "tail": len([q for q in sampled if len(q["text"]) >= 60]),
    }
    print(f"Sample distribution: head={_stats['head']}, mid={_stats['mid']}, tail={_stats['tail']}")

    model = os.environ.get("LLM_MODEL", "unknown")
    print(f"Running B8 baseline with model={model}...")
    results = run_baseline(sampled, output_path)
    print(f"Results saved to {output_path}")
