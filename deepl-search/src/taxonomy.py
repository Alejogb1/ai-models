"""
Taxonomy Skeleton (YQT-compatible, 8->64->512->3,843)
======================================================
Generates the full hierarchical tree structure. Swappable with real YQT data.
"""

import json
from dataclasses import dataclass, field
from typing import Optional


# L1 category names (generic — replace with real YQT names when available)
L1_NAMES = [
    "Arts & Entertainment",
    "Business & Finance",
    "Computers & Technology",
    "Education & Reference",
    "Food & Dining",
    "Health & Fitness",
    "Shopping & Commerce",
    "Travel & Local",
]

# L2 sub-category names (8 per L1)
L2_NAMES = {
    0: ["Visual Arts", "Performing Arts", "Music", "Movies", "TV", "Literature", "Comics & Animation", "Celebrities"],
    1: ["Investing", "Banking", "Insurance", "Real Estate", "Accounting", "Small Business", "Careers & Jobs", "Economy"],
    2: ["Software", "Hardware", "Programming", "Networking", "Cybersecurity", "AI & Data", "Mobile", "Cloud & DevOps"],
    3: ["K-12", "Higher Education", "Online Learning", "Research", "Dictionaries & Thesauri", "How-To Guides", "Academic Subjects", "Test Prep"],
    4: ["Restaurants", "Recipes", "Cooking Tips", "Beverages", "Nutrition", "Cuisine Types", "Dining Out", "Food Science"],
    5: ["Exercise & Workouts", "Mental Health", "Medical Conditions", "Medications", "Alternative Medicine", "Nutrition & Diet", "Wellness", "Senior Health"],
    6: ["Clothing", "Electronics", "Home & Garden", "Beauty Products", "Sports Gear", "Books & Media", "Toys & Hobbies", "Groceries"],
    7: ["Destinations", "Hotels", "Flight Booking", "Public Transit", "Maps & Navigation", "Local Services", "Events", "Weather"],
}


@dataclass
class TaxonomyNode:
    id: str
    name: str
    level: int
    children: list["TaxonomyNode"] = field(default_factory=list)
    parent: Optional["TaxonomyNode"] = None

    def path(self) -> list[str]:
        parts = []
        node = self
        while node:
            parts.append(node.id)
            node = node.parent
        return list(reversed(parts))

    def path_names(self) -> list[str]:
        parts = []
        node = self
        while node:
            parts.append(node.name)
            node = node.parent
        return list(reversed(parts))


def build_skeleton() -> TaxonomyNode:
    root = TaxonomyNode(id="root", name="Intent Taxonomy", level=0)

    for l1_idx in range(8):
        l1_name = L1_NAMES[l1_idx]
        l1_id = f"A{l1_idx+1}"
        l1 = TaxonomyNode(id=l1_id, name=l1_name, level=1, parent=root)
        root.children.append(l1)

        for l2_idx in range(8):
            l2_name = L2_NAMES[l1_idx][l2_idx]
            l2_id = f"{l1_id}.B{l2_idx+1}"
            l2 = TaxonomyNode(id=l2_id, name=l2_name, level=2, parent=l1)
            l1.children.append(l2)

            for l3_idx in range(8):
                l3_name = f"Subcategory {l3_idx+1}"
                l3_id = f"{l2_id}.C{l3_idx+1}"
                l3 = TaxonomyNode(id=l3_id, name=l3_name, level=3, parent=l2)
                l2.children.append(l3)

                # L4: exactly 3,843 leaves: 259 L3s with 8, 253 with 7
                l3_global_idx = (l1_idx * 64) + (l2_idx * 8) + l3_idx
                n_l4 = 8 if l3_global_idx < 259 else 7
                for l4_idx in range(n_l4):
                    l4_name = f"Intent {l4_idx+1}"
                    l4_id = f"{l3_id}.D{l4_idx+1}"
                    l4 = TaxonomyNode(id=l4_id, name=l4_name, level=4, parent=l3)
                    l3.children.append(l4)

    return root


def count_leaves(node: TaxonomyNode) -> int:
    if not node.children:
        return 1
    return sum(count_leaves(c) for c in node.children)


def count_by_level(node: TaxonomyNode, level: int) -> int:
    if node.level == level:
        return 1
    if not node.children:
        return 0
    return sum(count_by_level(c, level) for c in node.children)


def get_all_leaves(node: TaxonomyNode) -> list[TaxonomyNode]:
    results = []
    _collect_leaves(node, results)
    return results


def _collect_leaves(node: TaxonomyNode, results: list[TaxonomyNode]):
    if not node.children:
        results.append(node)
    for c in node.children:
        _collect_leaves(c, results)


def get_nodes_at_level(node: TaxonomyNode, level: int) -> list[TaxonomyNode]:
    results = []
    _collect_at_level(node, level, results)
    return results


def _collect_at_level(node: TaxonomyNode, level: int, results: list[TaxonomyNode]):
    if node.level == level:
        results.append(node)
    for c in node.children:
        _collect_at_level(c, level, results)


def to_skos_json(node: TaxonomyNode) -> dict:
    """Export taxonomy as SKOS JSON-LD."""
    nodes = []
    broader_edges = []

    def walk(n: TaxonomyNode):
        entry = {
            "@id": f"deepl:intent/{n.id}",
            "@type": "skos:Concept",
            "skos:prefLabel": {"@value": n.name, "@language": "en"},
            "skos:notation": n.id,
            "deepl:level": n.level,
        }
        if n.level > 0 and n.parent and n.parent.id != "root":
            broader_edges.append({
                "source": n.id,
                "target": n.parent.id,
            })
        nodes.append(entry)
        for c in n.children:
            walk(c)

    walk(node)

    skos = {
        "@context": {
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "deepl": "https://deepl-search.ai/ns/",
        },
        "@graph": nodes,
    }

    return skos


if __name__ == "__main__":
    root = build_skeleton()
    l1 = count_by_level(root, 1)
    l2 = count_by_level(root, 2)
    l3 = count_by_level(root, 3)
    leaves = count_leaves(root)
    print(f"L1: {l1}, L2: {l2}, L3: {l3}, L4 (leaves): {leaves}")
    print(f"Branching L1->L2: {l2/l1:.2f}")
    print(f"Branching L2->L3: {l3/l2:.2f}")
    print(f"Branching L3->L4: {leaves/l3:.2f}")

    # Export SKOS
    skos = to_skos_json(root)
    out_path = __file__.replace(".py", "_skos.json")
    with open(out_path, "w") as f:
        json.dump(skos, f, indent=2)
    print(f"SKOS exported to {out_path}: {len(skos['@graph'])} concepts")
