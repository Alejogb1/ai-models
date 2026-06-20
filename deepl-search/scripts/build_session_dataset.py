"""Build session-structured dataset from MS MARCO queries.

Creates synthetic sessions by grouping queries with similar topics.
Output: deepl-search/data/session_dataset.jsonl

Each session: {session_id, queries: [q1, q2, q3], target_intent (optional)}
"""

import csv
import json
import random
import os
from collections import defaultdict


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


def extract_topic_keywords(text: str) -> str:
    stopwords = {"what", "is", "the", "how", "to", "a", "an", "of", "in",
                 "for", "on", "with", "at", "by", "from", "do", "does",
                 "can", "are", "was", "were", "will", "would", "could",
                 "should", "has", "have", "had", "did", "be", "or", "and",
                 "not", "no", "but", "if", "so", "about", "get", "why",
                 "where", "when", "who", "which", "that", "this", "all",
                 "some", "any", "much", "many", "than", "too", "very",
                 "just", "also", "more", "most", "other", "such", "only",
                 "own", "same", "into", "over", "after", "before", "between"}
    words = text.lower().split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return keywords[0] if keywords else ""


def build_sessions(queries, num_sessions=1000, queries_per_session=3):
    grouped = defaultdict(list)
    for q in queries:
        topic = extract_topic_keywords(q["text"])
        if topic:
            grouped[topic].append(q)
    topic_groups = [(t, qs) for t, qs in grouped.items() if len(qs) >= queries_per_session]
    random.shuffle(topic_groups)
    sessions = []
    session_id = 0
    for topic, qs in topic_groups:
        if len(sessions) >= num_sessions:
            break
        sampled = random.sample(qs, queries_per_session)
        sessions.append({
            "session_id": f"session_{session_id:05d}",
            "topic": topic,
            "queries": [q["text"] for q in sampled],
            "query_ids": [q["id"] for q in sampled],
        })
        session_id += 1
    return sessions


def save_sessions(sessions, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for s in sessions:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')
    print(f"Saved {len(sessions)} sessions to {output_path}")


if __name__ == "__main__":
    queries_path = os.environ.get(
        "QUERIES_PATH",
        os.path.expanduser(r"~\.ir_datasets\msmarco-passage\train\queries.tsv")
    )
    output_path = os.environ.get(
        "OUTPUT_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "session_dataset.jsonl")
    )
    num_sessions = int(os.environ.get("NUM_SESSIONS", "1000"))

    print("Loading queries...")
    all_queries = load_queries(queries_path, max_queries=50000)
    print(f"Loaded {len(all_queries):,} queries")

    print(f"Building {num_sessions} sessions...")
    sessions = build_sessions(all_queries, num_sessions=num_sessions)
    save_sessions(sessions, output_path)

    # Stats
    lengths = [len(s["queries"]) for s in sessions]
    print(f"Sessions built: {len(sessions)}")
    print(f"Unique topics: {len(set(s['topic'] for s in sessions))}")
    print(f"Avg queries/session: {sum(lengths)/len(lengths):.1f}")
