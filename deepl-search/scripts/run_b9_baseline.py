"""B9 Baseline: Embedding classifier with improved class descriptions.

Re-runs the embedding classifier (all-MiniLM-L6-v2) with realistic
class descriptions to quantify the confounder cost of generic placeholders.

Usage:
    python scripts/run_b9_baseline.py

Output: deepl-search/experiments/b9_baseline_results.json
"""

import json
import os
import csv
import random
from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer


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

L2_DESCRIPTIONS = {
    "Arts & Entertainment": [
        "Visual Arts: queries about painting, photography, sculpture, art exhibitions, art history, and art supplies.",
        "Performing Arts: queries about theater, dance, opera, ballet, musical theater, and stage production.",
        "Music: queries about songs, artists, albums, concerts, lyrics, music genres, and music production.",
        "Movies: queries about specific movies, actors, directors, ratings, showtimes, reviews, and film production.",
        "Television: queries about TV shows, episodes, networks, streaming services, and TV personalities.",
        "Literature: queries about fiction, non-fiction, poetry, book reviews, literary criticism, and publishing.",
        "Comics & Animation: queries about comic books, anime, manga, webcomics, cartoons, and animation studios.",
        "Celebrities: queries about famous people, gossip, fashion, relationships, influencers, and entertainment news.",
    ],
    "Business & Finance": [
        "Investing: queries about stocks, bonds, mutual funds, options trading, retirement investing, and cryptocurrency.",
        "Banking: queries about checking accounts, savings accounts, credit cards, online banking, mortgages, and personal loans.",
        "Insurance: queries about health, life, auto, home, and travel insurance policies and claims.",
        "Real Estate: queries about homes for sale, rentals, property management, home buying, selling, and property taxes.",
        "Accounting: queries about tax preparation, bookkeeping, payroll, auditing, accounting software, and CPA.",
        "Small Business: queries about business plans, startup funding, marketing, licensing, e-commerce, and freelancing.",
        "Careers & Jobs: queries about job search, resume writing, interview tips, salary negotiation, remote work, and professional development.",
        "Economy: queries about economic news, GDP, inflation, employment, trade policy, Federal Reserve, and economic indicators.",
    ],
    "Computers & Technology": [
        "Software: queries about operating systems, office software, graphics software, productivity tools, and software reviews.",
        "Hardware: queries about desktops, laptops, tablets, peripherals, components, storage, and monitors.",
        "Programming: queries about programming languages, web development, mobile development, DevOps tools, and coding tutorials.",
        "Networking: queries about network protocols, WiFi, routers, network security, VPN, DNS, and cloud networking.",
        "Cybersecurity: queries about antivirus, firewalls, encryption, password security, data breaches, and ethical hacking.",
        "AI & Data: queries about machine learning, deep learning, data science, big data, AI ethics, and data visualization.",
        "Mobile: queries about smartphones, mobile apps, iOS, Android, mobile reviews, app development, and mobile gaming.",
        "Cloud & DevOps: queries about cloud computing, AWS, Azure, Docker, Kubernetes, CI/CD, and cloud security.",
    ],
    "Education & Reference": [
        "K-12: queries about elementary, middle, and high school education, curriculum, teaching resources, and special education.",
        "Higher Education: queries about college admissions, universities, graduate school, online degrees, financial aid, and academic majors.",
        "Online Learning: queries about MOOC courses, video tutorials, coding bootcamps, language learning, and online certifications.",
        "Research: queries about academic papers, research methods, scientific studies, peer review, research grants, and laboratories.",
        "Dictionaries & Thesauri: queries about word definitions, translations, encyclopedic entries, grammar guides, and citation formats.",
        "How-To Guides: queries about DIY projects, tutorials, life hacks, instructional videos, step-by-step guides, and FAQs.",
        "Academic Subjects: queries about math, science, history, English, social studies, foreign languages, and computer science.",
        "Test Prep: queries about SAT, ACT, GRE, GMAT, LSAT, MCAT prep, test strategies, and practice tests.",
    ],
    "Food & Dining": [
        "Restaurants: queries about fast food, casual dining, fine dining, cafes, restaurant reviews, and local eateries.",
        "Recipes: queries about main dishes, appetizers, desserts, baking, grilling, quick meals, and international recipes.",
        "Cooking Tips: queries about cooking techniques, kitchen tools, food preparation, meal planning, and cooking for beginners.",
        "Beverages: queries about coffee, tea, soda, juice, wine, beer, cocktails, and non-alcoholic drinks.",
        "Nutrition: queries about dietary guidelines, vitamins, supplements, superfoods, meal planning, and dietary restrictions.",
        "Cuisine Types: queries about Italian, Chinese, Mexican, Indian, Japanese, French, Thai, and American cuisine.",
        "Dining Out: queries about restaurant guides, food delivery, takeout, food trucks, dining deals, and reservations.",
        "Food Science: queries about food chemistry, food safety, food processing, GMO, organic food, and food technology.",
    ],
    "Health & Fitness": [
        "Exercise & Workouts: queries about strength training, cardio, yoga, pilates, home workouts, gym equipment, and workout plans.",
        "Mental Health: queries about anxiety, depression, therapy, mindfulness, meditation, stress management, and ADHD.",
        "Medical Conditions: queries about heart disease, diabetes, cancer, allergies, arthritis, asthma, and infectious diseases.",
        "Medications: queries about prescription drugs, over-the-counter medicine, drug interactions, side effects, and vaccines.",
        "Alternative Medicine: queries about acupuncture, chiropractic, herbal medicine, homeopathy, massage therapy, and ayurveda.",
        "Nutrition & Diet: queries about weight loss, diet plans, keto, vegan, paleo, Mediterranean diet, and intermittent fasting.",
        "Wellness: queries about sleep health, stress reduction, self-care, holistic health, preventive care, and health coaching.",
        "Senior Health: queries about aging, elder care, long-term care, senior fitness, memory loss, Medicare, and senior nutrition.",
    ],
    "Shopping & Commerce": [
        "Clothing: queries about men's, women's, and children's clothing, casual wear, formal wear, activewear, and shoes.",
        "Electronics: queries about smartphones, laptops, tablets, headphones, smart home devices, cameras, and TVs.",
        "Home & Garden: queries about gardening, home decor, furniture, kitchen appliances, home improvement, and storage.",
        "Beauty Products: queries about skincare, makeup, hair care, fragrance, nail care, beauty tools, and organic beauty.",
        "Sports Gear: queries about footwear, apparel, equipment, fitness trackers, sporting goods, and outdoor gear.",
        "Books & Media: queries about fiction and non-fiction books, ebooks, audiobooks, music albums, and video games.",
        "Toys & Hobbies: queries about action figures, board games, video games, collectibles, crafts, LEGO, and model kits.",
        "Groceries: queries about fresh produce, meat and seafood, dairy, bakery, frozen foods, pantry staples, and snacks.",
    ],
    "Travel & Local": [
        "Destinations: queries about travel locations in North America, Europe, Asia, Africa, and other regions.",
        "Hotels: queries about hotel reviews, hotel booking, luxury and budget hotels, resorts, hostels, and bed and breakfast.",
        "Flight Booking: queries about airlines, flight deals, airports, booking tips, first class, and flight status.",
        "Public Transit: queries about buses, trains, subways, taxis, ride sharing, transit maps, and commuting.",
        "Maps & Navigation: queries about GPS, street maps, satellite view, traffic, directions, and navigation apps.",
        "Local Services: queries about plumbers, electricians, doctors, dentists, mechanics, cleaners, and lawyers.",
        "Events: queries about concerts, festivals, conferences, sports events, cultural events, and event tickets.",
        "Weather: queries about forecasts, severe weather, climate, radar, hurricanes, and air quality.",
    ],
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


class EmbeddingClassifier:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.class_embeddings = None
        self.class_names = []
        self.class_level = None

    def build_index(self, class_descriptions: Dict[str, List[str]], level: str = "L1"):
        self.class_level = level
        self.class_names = []
        texts = []
        if level == "L1":
            for cat, desc in class_descriptions.items():
                self.class_names.append(cat)
                texts.append(desc)
        elif level == "L2":
            for cat, subcats in class_descriptions.items():
                for subcat in subcats:
                    self.class_names.append(subcat.split(":")[0].strip())
                    texts.append(subcat)
        self.class_embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        self.class_embeddings = self.class_embeddings / np.linalg.norm(self.class_embeddings, axis=1, keepdims=True)

    def predict(self, queries: List[str]) -> Dict:
        q_embeds = self.model.encode(queries, convert_to_numpy=True, show_progress_bar=False)
        q_embeds = q_embeds / np.linalg.norm(q_embeds, axis=1, keepdims=True)
        sims = q_embeds @ self.class_embeddings.T
        predictions = []
        for i in range(len(queries)):
            sim = sims[i]
            top_idx = np.argmax(sim)
            predictions.append({
                "query": queries[i],
                "predicted_class": self.class_names[top_idx],
                "confidence": float(sim[top_idx]),
                "confidence_distribution": {self.class_names[j]: float(sim[j])
                                            for j in range(len(self.class_names))},
                "entropy": float(-np.sum(np.exp(sim) / np.sum(np.exp(sim)) *
                                         np.log(np.exp(sim) / np.sum(np.exp(sim)) + 1e-10))),
            })
        return {
            "predictions": predictions,
            "mean_confidence": float(np.mean([p["confidence"] for p in predictions])),
            "std_confidence": float(np.std([p["confidence"] for p in predictions])),
            "mean_nonzero_per_query": float(np.mean([sum(1 for v in p["confidence_distribution"].values() if v > 0)
                                           for p in predictions])),
        }


def run_experiment():
    queries_path = os.environ.get(
        "QUERIES_PATH",
        os.path.expanduser(r"~\.ir_datasets\msmarco-passage\train\queries.tsv")
    )
    output_path = os.environ.get(
        "OUTPUT_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "experiments", "b9_baseline_results.json")
    )

    print("Loading queries...")
    all_queries = load_queries(queries_path, max_queries=2000)
    print(f"Loaded {len(all_queries)} queries")

    print("Initializing embedding classifier...")
    clf = EmbeddingClassifier()

    all_results = {}

    for level in ["L1", "L2"]:
        print(f"\n=== {level} Classification with improved descriptions ===")
        descs = L1_DESCRIPTIONS if level == "L1" else L2_DESCRIPTIONS
        n_classes = sum(len(v) for v in descs.values()) if isinstance(list(descs.values())[0], list) else len(descs)
        print(f"Building index for {n_classes} classes...")
        clf.build_index(descs, level=level)

        queries = [q["text"] for q in all_queries]
        results = clf.predict(queries)

        confidences = [p["confidence"] for p in results["predictions"]]
        top1_classes = [p["predicted_class"] for p in results["predictions"]]
        class_counts = {}
        for c in top1_classes:
            class_counts[c] = class_counts.get(c, 0) + 1

        all_results[level] = {
            "n_classes": n_classes,
            "n_queries": len(queries),
            "mean_confidence": results["mean_confidence"],
            "std_confidence": results["std_confidence"],
            "mean_nonzero_per_query": results["mean_nonzero_per_query"],
            "min_confidence": float(np.min(confidences)),
            "max_confidence": float(np.max(confidences)),
            "all_confidences": [float(c) for c in confidences],
            "confidence_bins": {
                "0_0.05": int(sum(1 for c in confidences if c < 0.05)),
                "0.05_0.10": int(sum(1 for c in confidences if 0.05 <= c < 0.10)),
                "0.10_0.15": int(sum(1 for c in confidences if 0.10 <= c < 0.15)),
                "0.15_0.20": int(sum(1 for c in confidences if 0.15 <= c < 0.20)),
                "0.20_0.30": int(sum(1 for c in confidences if 0.20 <= c < 0.30)),
                "0.30_0.50": int(sum(1 for c in confidences if 0.30 <= c < 0.50)),
                "0.50_1.00": int(sum(1 for c in confidences if 0.50 <= c)),
            },
            "top_classes_share": {k: v / len(queries) for k, v in
                                  sorted(class_counts.items(), key=lambda x: -x[1])[:10]},
            "effective_K": sum(1 for v in class_counts.values() if v / len(queries) > 0.01),
        }
        print(f"  Mean confidence: {all_results[level]['mean_confidence']:.4f}")
        print(f"  Mean non-zero per query: {all_results[level]['mean_nonzero_per_query']:.1f}")
        print(f"  Max confidence: {all_results[level]['max_confidence']:.4f}")
        print(f"  Effective K (>1% share): {all_results[level]['effective_K']}")

    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    # Compare to Phase 1 (generic descriptions) if available
    phase1_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "experiments", "exp3_granularity_sweep.json")
    if os.path.exists(phase1_path):
        with open(phase1_path) as f:
            phase1 = json.load(f)
        print("\n=== Comparison with Phase 1 (generic descriptions) ===")
        for level in ["L1", "L2"]:
            p1_key = f"K={8 if level == 'L1' else 64}"
            if p1_key in phase1:
                p1_conf = phase1[p1_key].get("mean_confidence", 0)
                print(f"  {level} Phase 1 confidence: {p1_conf:.4f} -> B9 confidence: {all_results[level]['mean_confidence']:.4f}")


if __name__ == "__main__":
    run_experiment()
