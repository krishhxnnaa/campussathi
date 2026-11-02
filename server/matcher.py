import re
from typing import List, Dict, Any

# Common Indic & English synonyms/terms for campus lost & found
SYNONYM_MAP = {
    # Watches & Timepieces
    "ghadi": "watch",
    "ghari": "watch",
    "wristwatch": "watch",
    "smartwatch": "watch",
    "analog": "watch",
    "timepiece": "watch",
    
    # Water Bottles
    "paani": "water",
    "pani": "water",
    "botol": "bottle",
    "thermos": "bottle",
    "flask": "bottle",
    
    # Eyewear
    "chashma": "glasses",
    "spectacles": "glasses",
    "specs": "glasses",
    "goggles": "glasses",
    
    # Wallets & Bags
    "batua": "wallet",
    "purse": "wallet",
    "jhola": "bag",
    "backpack": "bag",
    
    # Audio & Electronics
    "earphones": "airpods",
    "earphone": "airpods",
    "earbuds": "airpods",
    "airpod": "airpods",
    "airpods": "airpods",
    "headphone": "airpods",
    "headphones": "airpods",
    "tws": "airpods",
    "pods": "airpods",
    
    # Stationery
    "kalam": "pen",
    "ballpoint": "pen",
    "kitaab": "book",
    "pustak": "book",
    "notebook": "book",
    "register": "book",
    "calc": "calculator",
    "scientific": "calculator",
    
    # Chargers & Cables
    "adapter": "charger",
    "cable": "charger",
    "wire": "charger",
    "power": "charger",
    
    # Keys & Cards
    "chabi": "keys",
    "chaabi": "keys",
    "key": "keys",
    "idcard": "card",
    "id": "card"
}

STOPWORDS = {
    "i", "lost", "found", "my", "a", "an", "the", "in", "at", "on", "near", "around",
    "from", "to", "with", "and", "or", "of", "by",
    "mera", "meri", "kahi", "tha", "thi", "hai", "ke", "ki", "ka", "ko", "me", "main",
    "please", "help", "find", "search", "looking", "for", "item", "someone", "anyone"
}

# Known item entities to enforce entity integrity in multi-term searches
KNOWN_ITEM_ENTITIES = {
    "watch", "bottle", "wallet", "airpods", "calculator", "charger",
    "pen", "book", "keys", "glasses", "bag", "laptop", "card", "phone"
}

def tokenize(text: str) -> List[str]:
    if not text:
        return []
    words = re.findall(r"\w+", text.lower())
    tokens = []
    for w in words:
        if w in STOPWORDS:
            continue
        canonical = SYNONYM_MAP.get(w, w)
        tokens.append(canonical)
    return tokens

def match_and_rank_reports(query_text: str, candidate_reports: List[Dict[str, Any]], target_type: str = None) -> List[Dict[str, Any]]:
    """
    Strict, conservative relevance ranking.
    - If the user specifies an item entity (e.g. watch, bottle, wallet), candidates MUST match that entity.
    - Pure location overlap (e.g. 'library') will NEVER return an unrelated item (e.g. charger when searching for a watch).
    - Unrelated queries return an empty list.
    - Masks all private verification details and contact info.
    """
    clean_query = query_text.strip().lower()
    query_tokens = set(tokenize(clean_query))
    if not query_tokens:
        return []

    # Identify if query specifies any known item entities
    query_item_entities = query_tokens.intersection(KNOWN_ITEM_ENTITIES)

    results = []

    for report in candidate_reports:
        item_name = report.get("item_name", "").lower()
        category = report.get("category", "").lower()
        color = report.get("color", "").lower()
        location = report.get("location", "").lower()
        description = report.get("description", "").lower()

        name_tokens = set(tokenize(item_name))
        cat_tokens = set(tokenize(category))
        color_tokens = set(tokenize(color))
        loc_tokens = set(tokenize(location))
        desc_tokens = set(tokenize(description))

        # Combined item identity tokens for this record
        record_item_tokens = name_tokens.union(cat_tokens)

        # STRICT RELEVANCE RULE:
        # If the user's query mentions a specific item entity (e.g. watch, bottle, wallet, calculator),
        # this record MUST match that entity either in name, category, or core description.
        # Otherwise, discard immediately (prevents location-only false positives).
        if query_item_entities:
            matches_entity = bool(
                query_item_entities.intersection(record_item_tokens) or
                any(entity in item_name or entity in description for entity in query_item_entities)
            )
            if not matches_entity:
                continue

        score = 0
        match_reasons = []

        # 1. Direct Item Title Match (Weight: 45 pts)
        name_matches = query_tokens.intersection(name_tokens)
        if name_matches:
            score += 45
            match_reasons.append(f"Item name matches: {', '.join(name_matches)}")
        elif any(t in item_name for t in query_tokens if len(t) > 2):
            score += 30
            match_reasons.append("Item name keyword match")

        # 2. Category Match (Weight: 15 pts)
        cat_matches = query_tokens.intersection(cat_tokens)
        if cat_matches:
            score += 15
            match_reasons.append(f"Category: {report.get('category')}")

        # 3. Color Match (Weight: 20 pts)
        color_matches = query_tokens.intersection(color_tokens)
        if color_matches:
            score += 20
            match_reasons.append(f"Color: {report.get('color')}")
        elif color and any(c in clean_query for c in color_tokens):
            score += 15
            match_reasons.append(f"Color: {report.get('color')}")

        # 4. Location Match (Weight: 25 pts)
        loc_matches = query_tokens.intersection(loc_tokens)
        if loc_matches:
            score += 25
            match_reasons.append(f"Location: {', '.join(loc_matches)}")
        elif any(t in location for t in query_tokens if len(t) > 3):
            score += 15
            match_reasons.append("Location proximity match")

        # 5. General Description Match (Weight: 10 pts)
        desc_matches = query_tokens.intersection(desc_tokens) - name_matches - loc_matches
        if desc_matches:
            score += 10
            match_reasons.append(f"Description keywords: {', '.join(list(desc_matches)[:2])}")

        # Strict Thresholding:
        # A single keyword requires at least 35 points (meaning a direct item or location match)
        # Multi-term searches require at least 40 points
        min_threshold = 35 if len(query_tokens) == 1 else 40

        if score >= min_threshold:
            sanitized = {
                "id": report["id"],
                "report_type": report["report_type"],
                "item_name": report["item_name"],
                "category": report["category"],
                "color": report.get("color", ""),
                "description": report["description"],
                "location": report["location"],
                "approximate_time": report.get("approximate_time", ""),
                "image_path": report.get("image_path"),
                "is_demo": bool(report.get("is_demo", 0)),
                "created_at": report["created_at"],
                "status": report.get("status", "active"),
                "match_score": min(score, 100),
                "match_reasons": match_reasons
            }
            results.append(sanitized)

    # Sort descending by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:10]
