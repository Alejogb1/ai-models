"""Phase 6: Train Bi-Encoder on 500 Labeled Queries.

Trains the SimCSE-pretrained query encoder with MNR loss using
500 human-labeled queries matched to L2 class descriptions.

Usage:
    python scripts/train_bi_encoder.py

Output: deepl-search/models/bi_encoder_labeled/
        deepl-search/experiments/bi_encoder_training_results.json
"""

import os
import json
import csv
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel


LABELS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           "labels", "output", "labeled_records.jsonl")
QUERIES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "experiments", "msmarco_sample.txt")
MODEL_LOAD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "models", "simcse_query_encoder")
MODEL_SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "models", "bi_encoder_labeled")
RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "experiments", "bi_encoder_training_results.json")


# L2 descriptions (from the new IAB-based taxonomy)
L1_NAMES = [
    "Arts & Entertainment", "Business & Finance", "Computers & Technology",
    "Education & Reference", "Food & Dining", "Health & Fitness",
    "Shopping & Commerce", "Travel & Local",
]

L1_L2_DESCRIPTIONS = {
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

# Build flat L2 list: [(l1_name, l2_descriptor), ...]
L2_LIST = []
for l1_name in L1_NAMES:
    for desc in L1_L2_DESCRIPTIONS[l1_name]:
        l2_name = desc.split(":")[0].strip()
        L2_LIST.append((l1_name, l2_name, desc))

L2_NAME_TO_DESC = {name: desc for _, name, desc in L2_LIST}


class TransformerEncoder(nn.Module):
    def __init__(self, model_name_or_path: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__()
        self.model = AutoModel.from_pretrained(model_name_or_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.hidden_dim = self.model.config.hidden_size

    def forward(self, input_ids, attention_mask, **kwargs):
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
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


def load_data():
    """Load labeled queries and return (query_texts, l2_labels)."""
    queries_text = []
    with open(QUERIES_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            queries_text.append(line.strip())

    records = []
    with open(LABELS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))

    query_texts, l2_labels = [], []
    matched = 0
    for r in records:
        idx = r["record_index"]
        if idx < len(queries_text):
            query_texts.append(queries_text[idx])
            l2_labels.append(r["label"][1])
            matched += 1
    print(f"Matched {matched}/{len(records)} records to queries")
    return query_texts, l2_labels


def evaluate(model, query_texts, l2_labels, device="cpu"):
    """Evaluate: compare each query embedding to all 64 L2 descriptions,
    report top-1 L2 accuracy and mean confidence.
    """
    all_l2_descs = [desc for _, _, desc in L2_LIST]
    all_l2_names = [name for _, name, _ in L2_LIST]

    q_embeds = model.encode(query_texts, device=device)
    d_embeds = model.encode(all_l2_descs, device=device)

    q_embeds = q_embeds / np.linalg.norm(q_embeds, axis=1, keepdims=True)
    d_embeds = d_embeds / np.linalg.norm(d_embeds, axis=1, keepdims=True)

    sims = q_embeds @ d_embeds.T
    predictions = []
    correct = 0
    for i in range(len(query_texts)):
        sim = sims[i]
        top_idx = np.argmax(sim)
        predicted_l2 = all_l2_names[top_idx]
        confidence = float(sim[top_idx])
        predictions.append({
            "query": query_texts[i],
            "true_l2": l2_labels[i],
            "predicted_l2": predicted_l2,
            "confidence": confidence,
        })
        if predicted_l2 == l2_labels[i]:
            correct += 1

    confidences = [p["confidence"] for p in predictions]
    class_counts = {}
    for p in predictions:
        c = p["predicted_l2"]
        class_counts[c] = class_counts.get(c, 0) + 1

    return {
        "accuracy": correct / len(query_texts),
        "correct": correct,
        "total": len(query_texts),
        "mean_confidence": float(np.mean(confidences)),
        "std_confidence": float(np.std(confidences)),
        "max_confidence": float(np.max(confidences)),
        "min_confidence": float(np.min(confidences)),
        "effective_K": sum(1 for v in class_counts.values() if v / len(query_texts) > 0.01),
        "top10_classes_share": {k: round(v / len(query_texts), 3)
                                 for k, v in sorted(class_counts.items(),
                                                    key=lambda x: -x[1])[:10]},
    }


def run():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    print("Loading data...")
    query_texts, l2_labels = load_data()
    n = len(query_texts)
    print(f"Loaded {n} labeled queries")

    # Split into train/val
    indices = list(range(n))
    np.random.seed(42)
    np.random.shuffle(indices)
    val_size = n // 5
    train_idx = indices[val_size:]
    val_idx = indices[:val_size]
    train_queries = [query_texts[i] for i in train_idx]
    train_labels = [l2_labels[i] for i in train_idx]
    val_queries = [query_texts[i] for i in val_idx]
    val_labels = [l2_labels[i] for i in val_idx]
    print(f"Train: {len(train_queries)}, Val: {len(val_queries)}")

    # Load model
    print(f"Loading model from {MODEL_LOAD_PATH}...")
    model = TransformerEncoder(MODEL_LOAD_PATH)
    model.to(device)

    # Evaluate BEFORE training
    print("\n=== Evaluation BEFORE training ===")
    model.eval()
    before = evaluate(model, val_queries, val_labels, device=device)
    print(f"  L2 Accuracy: {before['accuracy']:.2%} ({before['correct']}/{before['total']})")
    print(f"  Mean conf: {before['mean_confidence']:.4f}")
    print(f"  Max conf: {before['max_confidence']:.4f}")
    print(f"  Effective K: {before['effective_K']}")

    # Training with MNR loss
    print("\n=== Training with MNR Loss ===")
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    batch_size = 32
    n_epochs = 10
    temperature = 0.05
    best_acc = 0.0

    all_l2_descs = [desc for _, _, desc in L2_LIST]

    class MNRDataset(Dataset):
        def __init__(self, queries, labels, l2_descs):
            self.queries = queries
            self.labels = labels
            self.l2_descs = l2_descs

        def __len__(self):
            return len(self.queries)

        def __getitem__(self, idx):
            return self.queries[idx], self.labels[idx]

    train_dataset = MNRDataset(train_queries, train_labels, all_l2_descs)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    for epoch in range(n_epochs):
        epoch_loss = 0.0
        n_batches = 0
        for batch_queries, batch_labels in train_loader:
            # Build positive descriptions for this batch
            batch_descs = [L2_NAME_TO_DESC.get(l, l) for l in batch_labels]

            # Tokenize queries and descriptions
            q_inputs = model.tokenizer(list(batch_queries), padding=True, truncation=True,
                                        max_length=128, return_tensors="pt")
            q_inputs = {k: v.to(device) for k, v in q_inputs.items()}

            d_inputs = model.tokenizer(batch_descs, padding=True, truncation=True,
                                        max_length=128, return_tensors="pt")
            d_inputs = {k: v.to(device) for k, v in d_inputs.items()}

            # Encode
            q_emb = model.forward(**q_inputs)
            d_emb = model.forward(**d_inputs)

            q_emb = F.normalize(q_emb, dim=1)
            d_emb = F.normalize(d_emb, dim=1)

            # MNR loss: sim[i,j] = cosine(q_i, d_j) / temperature
            # labels[i] = i (positive is the matching index)
            sim = torch.mm(q_emb, d_emb.t()) / temperature
            labels = torch.arange(len(batch_queries), device=device)

            loss = F.cross_entropy(sim, labels)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        print(f"Epoch {epoch+1}/{n_epochs}: loss={avg_loss:.4f}", end="")

        # Evaluate on validation set
        model.eval()
        val_results = evaluate(model, val_queries, val_labels, device=device)
        acc = val_results["accuracy"]
        print(f" val_acc={acc:.2%} mean_conf={val_results['mean_confidence']:.4f}")
        model.train()

        if acc > best_acc:
            best_acc = acc
            os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
            model.model.save_pretrained(MODEL_SAVE_PATH)
            model.tokenizer.save_pretrained(MODEL_SAVE_PATH)
            print(f"  New best model saved (acc={acc:.2%})")

    # Final evaluation
    print("\n=== Final Evaluation ===")
    model.eval()

    # Load best checkpoint
    if os.path.exists(os.path.join(MODEL_SAVE_PATH, "config.json")):
        model = TransformerEncoder(MODEL_SAVE_PATH)
        model.to(device)

    after = evaluate(model, val_queries, val_labels, device=device)
    print(f"  L2 Accuracy: {after['accuracy']:.2%} ({after['correct']}/{after['total']})")
    print(f"  Mean conf: {after['mean_confidence']:.4f}")
    print(f"  Max conf: {after['max_confidence']:.4f}")
    print(f"  Effective K: {after['effective_K']}")

    results = {
        "n_train": len(train_queries),
        "n_val": len(val_queries),
        "n_epochs": n_epochs,
        "batch_size": batch_size,
        "lr": 2e-5,
        "temperature": temperature,
        "model_path": str(MODEL_SAVE_PATH),
        "before_training": before,
        "after_training": after,
        "delta": {
            "accuracy": after["accuracy"] - before["accuracy"],
            "mean_confidence": after["mean_confidence"] - before["mean_confidence"],
            "max_confidence": after["max_confidence"] - before["max_confidence"],
            "effective_K": after["effective_K"] - before["effective_K"],
        },
        "best_val_accuracy": best_acc,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")


if __name__ == "__main__":
    run()
