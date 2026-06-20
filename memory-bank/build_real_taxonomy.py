"""
Build real L3/L4 names from IAB Content Taxonomy 3.0
=====================================================
Maps IAB categories into our 8 L1 × 64 L2 × 512 L3 × 3,843 L4 structure.
Fills gaps with generated names derived from L1/L2 context.
"""
import csv
import json
import os
from collections import defaultdict

PROJECT = r"C:\Users\ALEJOO\Documents\Gym IG Content Landing Page\ai-models"
IAB_PATH = r"E:\Content Taxonomy 3.0.tsv"
OUT_PATH = os.path.join(PROJECT, "labels", "taxonomy", "l3l4_mapping.json")
# Also copy to deepl-search/src for easy import
ALT_OUT = os.path.join(PROJECT, "deepl-search", "src", "taxonomy_l3l4_mapping.json")

# ── 1. Parse IAB TSV ──────────────────────────────────────────────
def parse_iab(path):
    """Parse IAB Content Taxonomy 3.0 TSV into structured dict."""
    # File has 2 header rows: merged header then sub-header.
    # Data starts on row 3 (0-indexed: line 2). Columns:
    # 0: Unique ID, 1: Parent, 2: Name, 3: Tier 1, 4: Tier 2, 5: Tier 3, 6: Tier 4, 7: Extension
    COL_UID = 0
    COL_PARENT = 1
    COL_NAME = 2
    COL_T1 = 3
    COL_T2 = 4
    COL_T3 = 5
    COL_T4 = 6

    entries = {}
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()

    # Skip first 2 header lines, parse tab-separated
    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue
        cols = line.split("\t")
        uid = cols[COL_UID].strip() if len(cols) > COL_UID else ""
        if not uid:
            continue
        entries[uid] = {
            "id": uid,
            "parent_id": cols[COL_PARENT].strip() if len(cols) > COL_PARENT else "",
            "name": cols[COL_NAME].strip() if len(cols) > COL_NAME else "",
            "tier1": cols[COL_T1].strip() if len(cols) > COL_T1 else "",
            "tier2": cols[COL_T2].strip() if len(cols) > COL_T2 else "",
            "tier3": cols[COL_T3].strip() if len(cols) > COL_T3 else "",
            "tier4": cols[COL_T4].strip() if len(cols) > COL_T4 else "",
        }
    return entries

def build_iab_tree(entries):
    """Build hierarchy: {tier1: {tier2: {tier3: [tier4...]}}}"""
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for eid, entry in entries.items():
        t1 = entry["tier1"]
        t2 = entry["tier2"]
        t3 = entry["tier3"]
        t4 = entry["tier4"]
        if t1 and t1 not in tree:
            tree[t1] = defaultdict(lambda: defaultdict(list))
        if t2:
            if t2 not in tree[t1]:
                tree[t1][t2] = defaultdict(list)
            if t3:
                if t3 not in tree[t1][t2]:
                    tree[t1][t2][t3] = []
                if t4:
                    if t4 not in tree[t1][t2][t3]:
                        tree[t1][t2][t3].append(t4)
    return tree

def collect_tier3_names(tree):
    """Collect all Tier 3 names per (Tier1, Tier2) for mapping."""
    mapping = defaultdict(list)
    for t1, t2_dict in tree.items():
        for t2, t3_dict in t2_dict.items():
            key = (t1, t2)
            mapping[key] = list(t3_dict.keys())
    return mapping

def collect_tier4_names(tree):
    """Collect all Tier 4 names per (Tier1, Tier2, Tier3)."""
    mapping = defaultdict(list)
    for t1, t2_dict in tree.items():
        for t2, t3_dict in t2_dict.items():
            for t3, t4_list in t3_dict.items():
                key = (t1, t2, t3)
                mapping[key] = t4_list
    return mapping

# ── 2. Our Taxonomy Structure ──────────────────────────────────────
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

# ── 3. Map IAB → Our Taxonomy ──────────────────────────────────────
# For each (L1, L2), define which IAB (Tier1, Tier2) categories to source L3/L4 names from.
# Tuple of (iab_tier1, iab_tier2) matches.
L2_TO_IAB = {
    # Arts & Entertainment
    (0, 0): [("Fine Art", "Design"), ("Fine Art", "Digital Arts"), ("Fine Art", "Fine Art Photography"), ("Fine Art", "Modern Art"), ("Fine Art", "Costume")],
    (0, 1): [("Fine Art", "Dance"), ("Fine Art", "Theater"), ("Fine Art", "Opera")],
    (0, 2): [("Entertainment", "Music")],
    (0, 3): [("Entertainment", "Movies"), ("Genres", "Action/Adventure"), ("Genres", "Science Fiction"), ("Genres", "Drama"), ("Genres", "Comedy"), ("Genres", "Horror")],
    (0, 4): [("Entertainment", "Television"), ("Genres", "Reality TV"), ("Genres", "Soap Opera"), ("Genres", "Talk Show")],
    (0, 5): [("Books and Literature", "Fiction"), ("Books and Literature", "Poetry"), ("Books and Literature", "Art and Photography"), ("Books and Literature", "Comics and Graphic Novels")],
    (0, 6): [("Books and Literature", "Comics and Graphic Novels"), ("Genres", "Animation & Anime")],
    (0, 7): [("Pop Culture",)],
    # Business & Finance
    (1, 0): [("Business and Finance", "Economy"), ("Personal Finance", "Personal Investing")],
    (1, 1): [("Business and Finance", "Business", "Business Banking & Finance"), ("Personal Finance", "Consumer Banking")],
    (1, 2): [("Personal Finance", "Insurance")],
    (1, 3): [("Real Estate",)],
    (1, 4): [("Business and Finance", "Business", "Business Accounting & Finance")],
    (1, 5): [("Business and Finance", "Business", "Small and Medium-sized Business"), ("Business and Finance", "Business", "Startups")],
    (1, 6): [("Careers",)],
    (1, 7): [("Business and Finance", "Economy")],
    # Computers & Technology
    (2, 0): [("Technology & Computing", "Computing", "Computer Software and Applications")],
    (2, 1): [("Technology & Computing", "Computing", "Desktops"), ("Technology & Computing", "Computing", "Laptops"), ("Technology & Computing", "Computing", "Computer Peripherals")],
    (2, 2): [("Technology & Computing", "Computing", "Programming Languages")],
    (2, 3): [("Technology & Computing", "Computing", "Computer Networking")],
    (2, 4): [("Technology & Computing", "Computing", "Information and Network Security")],
    (2, 5): [("Technology & Computing", "Artificial Intelligence"), ("Technology & Computing", "Computing", "Data Storage and Warehousing")],
    (2, 6): [("Technology & Computing", "Consumer Electronics", "Smartphones"), ("Technology & Computing", "Consumer Electronics", "Tablets and E-readers"), ("Technology & Computing", "Consumer Electronics", "Wearable Technology")],
    (2, 7): [("Technology & Computing", "Computing", "Internet", "Cloud Computing"), ("Technology & Computing", "Computing", "Internet", "Web Development"), ("Technology & Computing", "Computing", "Internet", "Web Hosting")],
    # Education & Reference
    (3, 0): [("Education", "Primary Education"), ("Education", "Secondary Education"), ("Education", "Homeschooling"), ("Education", "Special Education")],
    (3, 1): [("Education", "College Education")],
    (3, 2): [("Education", "Online Education"), ("Education", "Adult Education")],
    (3, 3): [("Science",)],
    (3, 4): [("Education", "Homework and Study"), ("Education", "Adult Education"), ("Books and Literature",)],  # broad reference
    (3, 5): [("Education", "Homework and Study"), ("Hobbies & Interests", "Workshops and Classes")],
    (3, 6): [("Science", "Biological Sciences"), ("Science", "Chemistry"), ("Science", "Physics"), ("Science", "Geography"), ("Science", "Space and Astronomy"), ("Science", "Environment"), ("Science", "Genetics"), ("Science", "Geology")],
    (3, 7): [("Education", "Educational Assessment", "Standardized Testing")],
    # Food & Dining
    (4, 0): [("Food & Drink", "Dining Out"), ("Attractions", "Bars & Restaurants")],
    (4, 1): [("Food & Drink", "Cooking"), ("Food & Drink", "World Cuisines")],
    (4, 2): [("Food & Drink", "Barbecues and Grilling"), ("Food & Drink", "Desserts and Baking"), ("Food & Drink", "Cooking")],
    (4, 3): [("Food & Drink", "Alcoholic Beverages"), ("Food & Drink", "Non-Alcoholic Beverages")],
    (4, 4): [("Food & Drink", "Healthy Cooking and Eating"), ("Food & Drink", "Food Movements"), ("Food & Drink", "Nutrition")],
    (4, 5): [("Food & Drink", "World Cuisines")],
    (4, 6): [("Food & Drink", "Dining Out")],
    (4, 7): [("Food & Drink", "Healthy Cooking and Eating"), ("Food & Drink", "Food Movements"), ("Food & Drink", "Food Allergies")],
    # Health & Fitness
    (5, 0): [("Healthy Living", "Fitness and Exercise")],
    (5, 1): [("Medical Health", "Diseases and Conditions", "Mental Health")],
    (5, 2): [("Medical Health", "Diseases and Conditions")],
    (5, 3): [("Medical Health", "Pharmaceutical Drugs")],
    (5, 4): [("Healthy Living", "Wellness", "Alternative Medicine")],
    (5, 5): [("Healthy Living", "Nutrition"), ("Healthy Living", "Weight Loss"), ("Food & Drink", "Healthy Cooking and Eating")],
    (5, 6): [("Healthy Living", "Wellness")],
    (5, 7): [("Healthy Living", "Senior Health"), ("Healthy Living", "Men's Health"), ("Healthy Living", "Women's Health"), ("Healthy Living", "Children's Health")],
    # Shopping & Commerce
    (6, 0): [("Style & Fashion", "Women's Fashion"), ("Style & Fashion", "Men's Fashion"), ("Style & Fashion", "Children's Clothing"), ("Style & Fashion", "Women's Clothing"), ("Style & Fashion", "Men's Clothing"), ("Style & Fashion", "Fashion Trends")],
    (6, 1): [("Technology & Computing", "Consumer Electronics")],
    (6, 2): [("Home & Garden",)],
    (6, 3): [("Style & Fashion", "Beauty")],
    (6, 4): [("Sports", "Sports Equipment"), ("Hobbies & Interests",)],
    (6, 5): [("Books and Literature",), ("Entertainment", "Movies"), ("Entertainment", "Music"), ("Entertainment", "Television"), ("Video Gaming",)],
    (6, 6): [("Shopping", "Children's Games and Toys"), ("Hobbies & Interests", "Games and Puzzles"), ("Hobbies & Interests", "Collecting"), ("Hobbies & Interests", "Model Toys")],
    (6, 7): [("Shopping", "Grocery Shopping"), ("Food & Drink",)],
    # Travel & Local
    (7, 0): [("Travel", "Travel Locations"), ("Attractions",)],
    (7, 1): [("Travel", "Travel Type", "Hotels and Motels")],
    (7, 2): [("Travel", "Travel Type", "Air Travel")],
    (7, 3): [("Travel", "Travel Type", "Rail Travel"), ("Travel", "Travel Type", "Public Transit")],
    (7, 4): [("Technology & Computing", "Computing", "Computer Software and Applications", "Maps & Navigation")],
    (7, 5): [("Travel", "Travel Preparation and Advice"), ("Local Services",)],
    (7, 6): [("Events",)],
    (7, 7): [("Science", "Weather")],
}

def get_deep_keys(tier1, tier2=None, tier3=None, tier4=None):
    """Build lookup keys for matching IAB entries at different depths."""
    keys = [tier1]
    if tier2:
        keys.append(tier2)
    if tier3:
        keys.append(tier3)
    if tier4:
        keys.append(tier4)
    return tuple(keys)

def match_iab_entries(entries, target_tiers):
    """Find IAB entries matching a target tuple at various depths."""
    results = []
    depth = len(target_tiers)
    for eid, entry in entries.items():
        entry_tiers = [entry["tier1"], entry["tier2"], entry["tier3"], entry["tier4"]]
        entry_tiers = [t for t in entry_tiers if t]  # remove blanks
        if len(entry_tiers) < depth:
            continue
        match = all(entry_tiers[i] == target_tiers[i] for i in range(depth))
        if match:
            results.append(entry)
    return results

# ── 4. Build L3/L4 Names ──────────────────────────────────────────
def generate_l3_name(l1_name, l2_name, l3_idx, iab_names):
    """Generate L3 name: prefer IAB name, fallback to descriptive."""
    if iab_names and l3_idx < len(iab_names):
        return iab_names[l3_idx]
    # Fallback: derive from L2
    l3_ideas = {
        "Visual Arts": ["Drawing & Painting", "Sculpture", "Photography", "Digital Art", "Art History", "Art Exhibitions", "Art Supplies", "Art Education"],
        "Performing Arts": ["Theater", "Dance", "Opera", "Ballet", "Musical Theater", "Performance Art", "Stage Production", "Auditions"],
        "Music": ["Music Genres", "Music Production", "Music Instruments", "Music Education", "Music Events", "Music Reviews", "Music History", "Music Streaming"],
        "Movies": ["Movie Genres", "Movie Reviews", "Movie Trailers", "Movie News", "Movie Rankings", "Movie History", "Film Festivals", "Movie Production"],
        "TV": ["TV Shows", "TV Reviews", "TV News", "TV Schedules", "Streaming Services", "TV Genres", "TV History", "TV Production"],
        "Literature": ["Fiction", "Non-Fiction", "Poetry", "Book Reviews", "Literary Criticism", "Publishing", "Book Events", "Reading Lists"],
        "Comics & Animation": ["Comic Books", "Anime", "Manga", "Webcomics", "Cartoons", "Animation Studios", "Comic Conventions", "Graphic Novels"],
        "Celebrities": ["Celebrity News", "Celebrity Gossip", "Celebrity Style", "Celebrity Relationships", "Celebrity Families", "Celebrity Deaths", "Celebrity Scandals", "Influencers"],
        "Investing": ["Stocks", "Bonds", "Mutual Funds", "Options Trading", "Retirement Investing", "Real Estate Investing", "Cryptocurrency", "Investment Advice"],
        "Banking": ["Checking Accounts", "Savings Accounts", "Credit Cards", "Online Banking", "Mortgages", "Personal Loans", "Bank Reviews", "Interest Rates"],
        "Insurance": ["Health Insurance", "Life Insurance", "Auto Insurance", "Home Insurance", "Travel Insurance", "Pet Insurance", "Insurance Advice", "Insurance Reviews"],
        "Real Estate": ["Homes for Sale", "Rentals", "Property Management", "Home Buying", "Home Selling", "Commercial Real Estate", "Real Estate Investing", "Property Taxes"],
        "Accounting": ["Tax Preparation", "Bookkeeping", "Payroll", "Auditing", "Accounting Software", "Financial Statements", "CPA", "Tax Law"],
        "Small Business": ["Business Plans", "Startup Funding", "Small Business Marketing", "Business Licenses", "E-commerce", "Freelancing", "Business Insurance", "Small Business Tools"],
        "Careers & Jobs": ["Job Search", "Resume Writing", "Interview Tips", "Career Change", "Salary Negotiation", "Remote Work", "Internships", "Professional Development"],
        "Economy": ["Economic News", "GDP", "Inflation", "Employment", "Trade Policy", "Federal Reserve", "Global Economy", "Economic Indicators"],
        "Software": ["Operating Systems", "Office Software", "Graphics Software", "Video Software", "Audio Software", "Productivity Tools", "Software Reviews", "Open Source"],
        "Hardware": ["Desktops", "Laptops", "Tablets", "Peripherals", "Components", "Storage", "Printers", "Monitors"],
        "Programming": ["Python", "JavaScript", "Java", "C++", "Web Development", "Mobile Development", "DevOps Tools", "Programming Tutorials"],
        "Networking": ["Network Protocols", "WiFi", "Routers", "Network Security", "VPN", "DNS", "Network Administration", "Cloud Networking"],
        "Cybersecurity": ["Antivirus", "Firewalls", "Encryption", "Password Security", "Data Breaches", "Ethical Hacking", "Security Certifications", "Privacy"],
        "AI & Data": ["Machine Learning", "Deep Learning", "Data Science", "Big Data", "AI Ethics", "Data Mining", "Data Visualization", "Data Engineering"],
        "Mobile": ["Smartphones", "Mobile Apps", "iOS", "Android", "Mobile Reviews", "Mobile Accessories", "App Development", "Mobile Gaming"],
        "Cloud & DevOps": ["Cloud Computing", "AWS", "Azure", "Docker", "Kubernetes", "CI/CD", "Infrastructure as Code", "Cloud Security"],
        "K-12": ["Elementary School", "Middle School", "High School", "Curriculum", "Teaching Resources", "Parenting & Education", "School Choice", "Special Education"],
        "Higher Education": ["College Admission", "Universities", "Community College", "Graduate School", "Online Degrees", "Study Abroad", "Financial Aid", "Academic Majors"],
        "Online Learning": ["MOOC Courses", "Video Tutorials", "Coding Bootcamps", "Language Learning", "Skill Development", "Certifications", "Virtual Classrooms", "E-Learning Tools"],
        "Research": ["Academic Papers", "Research Methods", "Scientific Studies", "Peer Review", "Research Grants", "Laboratories", "Data Analysis", "Research Ethics"],
        "Dictionaries & Thesauri": ["Online Dictionaries", "Thesauruses", "Encyclopedias", "Translation Tools", "Language Reference", "Word Origins", "Grammar Guides", "Citation Guides"],
        "Academic Subjects": ["Mathematics", "History", "Science", "English", "Social Studies", "Foreign Languages", "Arts Education", "Computer Science"],
        "Test Prep": ["SAT Prep", "ACT Prep", "GRE Prep", "GMAT Prep", "LSAT Prep", "MCAT Prep", "Test Strategies", "Practice Tests"],
        "Restaurants": ["Fast Food", "Casual Dining", "Fine Dining", "Cafes", "Restaurant Reviews", "Restaurant News", "Restaurant Chains", "Local Eateries"],
        "How-To Guides": ["DIY Projects", "Tutorials", "Guides", "Life Hacks", "Instructional Videos", "Step-by-Step Guides", "Tips & Tricks", "FAQs"],
        "Recipes": ["Main Dishes", "Appetizers", "Desserts", "Soups & Salads", "Baking", "Grilling", "Quick Meals", "International Recipes"],
        "Cooking Tips": ["Cooking Techniques", "Kitchen Tools", "Food Preparation", "Meal Planning", "Food Storage", "Cooking for Beginners", "Chef Tips", "Kitchen Safety"],
        "Beverages": ["Coffee", "Tea", "Soda", "Juice", "Wine", "Beer", "Cocktails", "Non-Alcoholic Drinks"],
        "Nutrition": ["Dietary Guidelines", "Vitamins", "Supplements", "Superfoods", "Meal Planning", "Calorie Counting", "Macros", "Dietary Restrictions"],
        "Cuisine Types": ["Italian", "Chinese", "Mexican", "Indian", "Japanese", "French", "Thai", "American"],
        "Dining Out": ["Restaurant Guides", "Food Delivery", "Takeout", "Buffet", "Food Trucks", "Dining Deals", "Reservations", "Outdoor Dining"],
        "Food Science": ["Food Chemistry", "Food Safety", "Food Processing", "Food Preservation", "Food Additives", "GMO", "Organic Food", "Food Technology"],
        "Exercise & Workouts": ["Strength Training", "Cardio", "Yoga", "Pilates", "Home Workouts", "Gym Equipment", "Personal Training", "Workout Plans"],
        "Mental Health": ["Anxiety", "Depression", "Therapy", "Mindfulness", "Meditation", "Stress Management", "PTSD", "ADHD"],
        "Medical Conditions": ["Heart Disease", "Diabetes", "Cancer", "Allergies", "Arthritis", "Asthma", "Infectious Diseases", "Autoimmune Disorders"],
        "Medications": ["Prescription Drugs", "Over-the-Counter", "Drug Interactions", "Side Effects", "Vaccines", "Antibiotics", "Pain Management", "Pharmacy"],
        "Alternative Medicine": ["Acupuncture", "Chiropractic", "Herbal Medicine", "Homeopathy", "Naturopathy", "Massage Therapy", "Aromatherapy", "Ayurveda"],
        "Nutrition & Diet": ["Weight Loss", "Diet Plans", "Keto", "Vegan", "Paleo", "Mediterranean Diet", "Intermittent Fasting", "Meal Replacement"],
        "Wellness": ["Sleep Health", "Stress Reduction", "Self-Care", "Holistic Health", "Mind-Body Connection", "Preventive Care", "Health Coaching", "Wellness Trends"],
        "Senior Health": ["Aging", "Elder Care", "Long-term Care", "Senior Fitness", "Memory Loss", "Osteoporosis", "Medicare", "Senior Nutrition"],
        "Clothing": ["Men's Clothing", "Women's Clothing", "Children's Clothing", "Casual Wear", "Formal Wear", "Activewear", "Outerwear", "Shoes"],
        "Electronics": ["Smartphones", "Laptops", "Tablets", "Headphones", "Smart Home", "Cameras", "Gaming Consoles", "TVs"],
        "Home & Garden": ["Gardening", "Home Decor", "Furniture", "Kitchen Appliances", "Home Improvement", "Lighting", "Bedding", "Storage"],
        "Beauty Products": ["Skincare", "Makeup", "Hair Care", "Fragrance", "Nail Care", "Beauty Tools", "Organic Beauty", "Beauty Reviews"],
        "Sports Gear": ["Footwear", "Apparel", "Equipment", "Accessories", "Team Gear", "Fitness Trackers", "Sporting Goods", "Outdoor Gear"],
        "Books & Media": ["Fiction Books", "Non-Fiction Books", "Ebooks", "Audiobooks", "Music Albums", "Movies & TV", "Video Games", "Magazines"],
        "Toys & Hobbies": ["Action Figures", "Board Games", "Video Games", "Collectibles", "Crafts", "LEGO", "Model Kits", "Outdoor Toys"],
        "Groceries": ["Fresh Produce", "Meat & Seafood", "Dairy", "Bakery", "Frozen Foods", "Pantry Staples", "Snacks", "Beverages"],
        "Destinations": ["North America", "Europe", "Asia", "Africa", "South America", "Australia", "Islands", "Polar Regions"],
        "Hotels": ["Hotel Reviews", "Hotel Booking", "Luxury Hotels", "Budget Hotels", "Boutique Hotels", "Resorts", "Hostels", "Bed & Breakfast"],
        "Flight Booking": ["Airlines", "Flight Deals", "Airports", "Booking Tips", "First Class", "Budget Airlines", "Flight Status", "Layovers"],
        "Public Transit": ["Buses", "Trains", "Subways", "Taxis", "Ride Sharing", "Transit Maps", "Commuting", "Fares & Passes"],
        "Maps & Navigation": ["GPS", "Street Maps", "Satellite View", "Traffic", "Directions", "Geolocation", "Navigation Apps", "Landmarks"],
        "Local Services": ["Plumbers", "Electricians", "Doctors", "Dentists", "Mechanics", "Cleaners", "Lawyers", "Pet Services"],
        "Events": ["Concerts", "Festivals", "Conferences", "Sports Events", "Cultural Events", "Community Events", "Ticketing", "Event Calendar"],
        "Weather": ["Forecasts", "Severe Weather", "Climate", "Radar", "Hurricanes", "Winter Weather", "Air Quality", "Historical Weather"],
    }
    return l3_ideas.get(l2_name, [f"{l2_name} - Topic {l3_idx+1}"])[l3_idx % 8]

def generate_l4_name(l1_name, l2_name, l3_name, l4_idx, iab_names):
    """Generate L4 name: prefer IAB Tier 4 name, fallback to descriptive."""
    if iab_names and l4_idx < len(iab_names):
        return iab_names[l4_idx]
    # Fallback: derive from L3
    return f"{l3_name} - Detail {l4_idx + 1}"

def build_taxonomy_mapping(entries, iab_tree):
    """Build complete L3/L4 name mapping."""
    t3_by_key = collect_tier3_names(iab_tree)
    t4_by_key = collect_tier4_names(iab_tree)

    mapping = {
        "source": "IAB Content Taxonomy 3.0 + generated fallbacks",
        "l3_names": {},
        "l4_names": {},
    }

    for l1_idx in range(8):
        l1_name = L1_NAMES[l1_idx]
        for l2_idx in range(8):
            l2_name = L2_NAMES[l1_idx][l2_idx]
            l2_key = (l1_idx, l2_idx)

            # Collect IAB names for this L2
            iab_refs = L2_TO_IAB.get(l2_key, [])
            iab_t3_pool = []
            iab_t4_pool = defaultdict(list)

            for ref in iab_refs:
                if len(ref) == 1:
                    # Only Tier 1 specified
                    for t1, t2_dict in iab_tree.items():
                        if t1 == ref[0] or t1.lower().startswith(ref[0].lower()):
                            for t2, t3_dict in t2_dict.items():
                                for t3, t4_list in t3_dict.items():
                                    if t3 not in iab_t3_pool:
                                        iab_t3_pool.append(t3)
                                    iab_t4_pool[t3].extend(t4_list)
                elif len(ref) == 2:
                    t1, t2 = ref
                    key = (t1, t2)
                    # Exact match or fuzzy
                    t3_names = t3_by_key.get(key, [])
                    # Also try partial match
                    if not t3_names:
                        for k, v in t3_by_key.items():
                            if k[0] == t1 and (t2.lower() in k[1].lower() or k[1].lower() in t2.lower()):
                                t3_names = v
                                break
                    for t3 in t3_names:
                        if t3 not in iab_t3_pool:
                            iab_t3_pool.append(t3)
                        k4 = (t1, t2, t3)
                        iab_t4_pool[t3].extend(t4_by_key.get(k4, []))
                elif len(ref) == 3:
                    t1, t2, t3 = ref
                    if t3 not in iab_t3_pool:
                        iab_t3_pool.append(t3)
                    k4 = (t1, t2, t3)
                    iab_t4_pool[t3].extend(t4_by_key.get(k4, []))
                elif len(ref) == 4:
                    t1, t2, t3, t4 = ref
                    if t3 not in iab_t3_pool:
                        iab_t3_pool.append(t3)
                    iab_t4_pool[t3].append(t4)

            # Assign L3 names
            for l3_idx in range(8):
                l3_id = f"A{l1_idx+1}.B{l2_idx+1}.C{l3_idx+1}"
                l3_name = generate_l3_name(l1_name, l2_name, l3_idx, iab_t3_pool)
                mapping["l3_names"][l3_id] = l3_name

                # Assign L4 names
                l3_global_idx = (l1_idx * 64) + (l2_idx * 8) + l3_idx
                n_l4 = 8 if l3_global_idx < 259 else 7
                l4_pool = iab_t4_pool.get(l3_name, [])
                # Deduplicate
                seen = set()
                l4_pool_dedup = []
                for name in l4_pool:
                    if name not in seen:
                        seen.add(name)
                        l4_pool_dedup.append(name)

                for l4_idx in range(n_l4):
                    l4_id = f"{l3_id}.D{l4_idx+1}"
                    l4_name = generate_l4_name(l1_name, l2_name, l3_name, l4_idx, l4_pool_dedup)
                    mapping["l4_names"][l4_id] = l4_name

    return mapping

def main():
    print("Parsing IAB taxonomy...")
    entries = parse_iab(IAB_PATH)
    print(f"  Loaded {len(entries)} entries")

    print("Building IAB tree...")
    iab_tree = build_iab_tree(entries)
    t1_count = len(iab_tree)
    t2_count = sum(len(v) for v in iab_tree.values())
    t3_count = sum(sum(len(v3) for v3 in v2.values()) for v2 in iab_tree.values())
    t4_count = sum(sum(sum(len(v4) for v4 in v3.values()) for v3 in v2.values()) for v2 in iab_tree.values())
    print(f"  T1: {t1_count}, T2: {t2_count}, T3: {t3_count}, T4: {t4_count}")

    print("Building taxonomy mapping...")
    mapping = build_taxonomy_mapping(entries, iab_tree)

    # Count
    l3_count = len(mapping["l3_names"])
    l4_count = len(mapping["l4_names"])
    print(f"  L3: {l3_count}, L4: {l4_count}")
    iab_sourced_l3 = sum(1 for v in mapping["l3_names"].values() if not v.startswith("Topic") and not v.endswith("Detail"))
    print(f"  IAB-sourced L3 names: {iab_sourced_l3}/{l3_count}")

    print(f"Writing to {OUT_PATH}...")
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"Writing to {ALT_OUT}...")
    os.makedirs(os.path.dirname(ALT_OUT), exist_ok=True)
    with open(ALT_OUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print("Done!")

if __name__ == "__main__":
    main()
