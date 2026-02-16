"""
Keyword Strategy Tool - Configuration
Supports multiple brands (Bash, etc.) with configurable modifiers and patterns.
"""

# Intent types for filtering (educational, consideration, conversion)
INTENT_TYPES = {
    "educational": {
        "modifiers": ["how to", "guide", "what is", "why", "tips", "learn", "tutorial", "how to choose"],
        "patterns": ["how to choose {product}", "{product} guide {location}", "what is {product}"],
    },
    "consideration": {
        "modifiers": ["reviews", "vs", "comparison", "best", "top", "guide", "which", "recommended"],
        "patterns": ["{product} reviews {location}", "best {product} {location}", "{product} comparison"],
    },
    "conversion": {
        "modifiers": ["for sale", "for sale online", "buy online", "shop online", "price", "deals", "specials", "sale", "discount", "best price", "cheap", "affordable"],
        "patterns": ["{product} for sale {location}", "buy {product} {location}", "{product} price {location}"],
    },
}

# Keyword types (what to generate)
KEYWORD_TYPES = ["location_based", "product_attribute", "intent_modifier", "question_format"]

# Default locations (can be extended by user)
DEFAULT_LOCATIONS = [
    "south africa",
    "in south africa",
    "cape town",
    "johannesburg",
    "durban",
    "pretoria",
    "online south africa",
]

# Default modifiers extracted from Bash.com patterns - customize per brand/region
DEFAULT_MODIFIERS = {
    "location": DEFAULT_LOCATIONS,
    "intent_commercial": [
        "for sale",
        "for sale online",
        "buy online",
        "shop online",
        "price",
        "price in south africa",
        "deals",
        "specials",
        "sale",
        "discount",
        "best price",
        "cheap",
        "affordable",
    ],
    "intent_consideration": [
        "reviews",
        "vs",
        "comparison",
        "best",
        "top",
        "guide",
        "how to choose",
        "which",
        "recommended",
    ],
    "temporal": [
        "black friday",
        "black friday deals",
        "2026",
        "2025",
    ],
    "attributes": [
        "king size",
        "queen size",
        "single",
        "double",
        "large",
        "small",
        "modern",
        "traditional",
        "luxury",
        "budget",
    ],
    "colors": [
        "black",
        "white",
        "grey",
        "gray",
        "blue",
        "green",
        "brown",
        "navy",
        "cream",
        "beige",
    ],
}

# Intent patterns for long-tail (consideration stage = high intent for content)
CONSIDERATION_PATTERNS = [
    "{product} {location}",
    "{product} for sale {location}",
    "{product} price {location}",
    "{product} reviews {location}",
    "{product} vs {alternative}",
    "best {product} {location}",
    "{product} {attribute} {location}",
    "{product} {color} {location}",
    "buy {product} {location}",
    "shop {product} {location}",
    "{product} deals {location}",
    "{product} specials {location}",
    "{product} {attribute} for sale",
    "where to buy {product} {location}",
    "{product} comparison {location}",
    "top {product} {location}",
]

# Minimum word count for long-tail (3+ words typically)
LONGTAIL_MIN_WORDS = 3

# Straider-ready export columns
STRAIDER_EXPORT_COLUMNS = [
    "keyword",
    "intent",
    "source",
    "product_url",
    "seo_title",
    "search_volume_estimate",
    "priority",
]
