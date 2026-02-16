"""
Keyword Strategy Tool - Programmatic Keyword Expansion
Generates thousands of long-tail keywords from seed data using modifier patterns.
"""

import itertools
from collections import Counter
from typing import Optional, List
from dataclasses import dataclass, field

from .config import (
    DEFAULT_MODIFIERS,
    DEFAULT_LOCATIONS,
    CONSIDERATION_PATTERNS,
    LONGTAIL_MIN_WORDS,
    INTENT_TYPES,
)
from .data_loaders import KeywordSource


@dataclass
class ExpandedKeyword:
    """A generated keyword with metadata."""
    keyword: str
    intent: str  # educational | consideration | conversion
    source_keyword: str
    source: str
    product_url: Optional[str] = None
    seo_title: Optional[str] = None
    priority: int = 0  # higher = more valuable


@dataclass
class GenerationSettings:
    """Settings for keyword generation."""
    intents: List[str] = field(default_factory=lambda: ["educational", "consideration", "conversion"])
    keyword_types: List[str] = field(default_factory=lambda: ["location_based", "product_attribute", "intent_modifier"])
    locations: List[str] = field(default_factory=lambda: list(DEFAULT_LOCATIONS))
    min_words: int = 3
    max_words: int = 0  # 0 = no limit


def _normalize_keyword(kw: str) -> str:
    """Normalize keyword for deduplication."""
    return " ".join(kw.lower().strip().split())


def _is_longtail(keyword: str, min_words: int = LONGTAIL_MIN_WORDS, max_words: int = 0) -> bool:
    """Check if keyword meets length criteria."""
    wc = len(keyword.split())
    if max_words and wc > max_words:
        return False
    return wc >= min_words


def _extract_core_product(phrase: str) -> str:
    """Extract core product term (remove location, for sale, etc.)."""
    words = phrase.lower().split()
    remove = {"south", "africa", "sale", "for", "online", "buy", "shop", "price", "deals", "specials"}
    return " ".join(w for w in words if w not in remove)


def _build_modifiers_from_settings(settings: Optional["GenerationSettings"]) -> dict:
    """Build modifier dict from GenerationSettings."""
    if not settings:
        return DEFAULT_MODIFIERS
    mods = dict(DEFAULT_MODIFIERS)
    mods["location"] = settings.locations or mods["location"]
    # Merge intent modifiers based on selected intents
    intent_commercial = []
    intent_consideration = []
    intent_educational = []
    for intent in settings.intents:
        if intent in INTENT_TYPES:
            it = INTENT_TYPES[intent]
            if intent == "conversion":
                intent_commercial.extend(it["modifiers"])
            elif intent == "consideration":
                intent_consideration.extend(it["modifiers"])
            elif intent == "educational":
                intent_educational.extend(it["modifiers"])
    mods["intent_commercial"] = list(dict.fromkeys(intent_commercial)) or mods["intent_commercial"]
    mods["intent_consideration"] = list(dict.fromkeys(intent_consideration)) or mods["intent_consideration"]
    mods["intent_educational"] = list(dict.fromkeys(intent_educational))
    return mods


def expand_with_modifiers(
    seed_keywords: list[str],
    modifiers: dict = None,
    max_per_seed: int = 50,
    min_word_count: int = LONGTAIL_MIN_WORDS,
    max_word_count: int = 0,
    settings: Optional["GenerationSettings"] = None,
) -> list[ExpandedKeyword]:
    """
    Programmatically expand seed keywords with location, intent, and attribute modifiers.
    Focus on long-tail (3+ words).
    """
    modifiers = modifiers or _build_modifiers_from_settings(settings) or DEFAULT_MODIFIERS
    min_w = min_word_count
    max_w = max_word_count or 999
    seen = set()
    results = []
    kw_types = (settings.keyword_types if settings else None) or ["location_based", "product_attribute", "intent_modifier"]

    for seed in seed_keywords:
        seed_norm = _normalize_keyword(seed)
        if not seed_norm or seed_norm in seen:
            continue
        seen.add(seed_norm)

        count = 0
        # Location modifiers (high priority for local SEO)
        if "location_based" in kw_types:
            for loc in modifiers.get("location", []):
                if count >= max_per_seed:
                    break
                kw = f"{seed_norm} {loc}".strip()
                if _is_longtail(kw, min_w, max_w) and kw not in seen:
                    seen.add(kw)
                    results.append(ExpandedKeyword(
                        keyword=kw,
                        intent="conversion" if any(x in kw for x in ["sale", "buy", "price"]) else "consideration",
                        source_keyword=seed,
                        source="programmatic_modifier",
                        priority=2 if "south africa" in loc.lower() or "africa" in loc.lower() else 1,
                    ))
                    count += 1

        # Intent commercial (conversion)
        if "intent_modifier" in kw_types:
            for intent in modifiers.get("intent_commercial", []):
                if count >= max_per_seed:
                    break
                for variant in [f"{seed_norm} {intent}", f"{intent} {seed_norm}"]:
                    if _is_longtail(variant, min_w, max_w) and variant not in seen:
                        seen.add(variant)
                        results.append(ExpandedKeyword(
                            keyword=variant,
                            intent="conversion",
                            source_keyword=seed,
                            source="programmatic_modifier",
                            priority=1,
                        ))
                        count += 1
                        break

        # Intent consideration (high value for content)
        if "intent_modifier" in kw_types:
            for intent in modifiers.get("intent_consideration", []):
                if count >= max_per_seed:
                    break
                kw = f"{seed_norm} {intent}".strip()
                if _is_longtail(kw, min_w, max_w) and kw not in seen:
                    seen.add(kw)
                    results.append(ExpandedKeyword(
                        keyword=kw,
                        intent="consideration",
                        source_keyword=seed,
                        source="programmatic_modifier",
                        priority=3,
                    ))
                    count += 1

        # Intent educational
        if "intent_modifier" in kw_types and modifiers.get("intent_educational"):
            for intent in modifiers.get("intent_educational", []):
                if count >= max_per_seed:
                    break
                kw = f"{seed_norm} {intent}".strip()
                if _is_longtail(kw, min_w, max_w) and kw not in seen:
                    seen.add(kw)
                    results.append(ExpandedKeyword(
                        keyword=kw,
                        intent="educational",
                        source_keyword=seed,
                        source="programmatic_modifier",
                        priority=2,
                    ))
                    count += 1

        # Color + product (product_attribute)
        if "product_attribute" in kw_types:
            core = _extract_core_product(seed_norm)
            if core and core != seed_norm:
                for color in modifiers.get("colors", [])[:5]:
                    if count >= max_per_seed:
                        break
                    kw = f"{color} {core}".strip()
                    if _is_longtail(kw, min_w, max_w) and kw not in seen:
                        seen.add(kw)
                        results.append(ExpandedKeyword(
                            keyword=kw,
                            intent="conversion",
                            source_keyword=seed,
                            source="programmatic_modifier",
                            priority=1,
                        ))
                        count += 1

    return results


def extract_n_grams(queries: list[str], n: int = 2, min_freq: int = 2) -> list[str]:
    """
    Extract common n-grams from queries to discover product + modifier patterns.
    """
    ngrams = []
    for q in queries:
        words = q.lower().split()
        for i in range(len(words) - n + 1):
            ngrams.append(" ".join(words[i : i + n]))

    counts = Counter(ngrams)
    return [ng for ng, c in counts.most_common(200) if c >= min_freq]


def expand_from_patterns(
    product_terms: list[str],
    modifiers: dict = None,
    patterns: list[str] = None,
    min_word_count: int = LONGTAIL_MIN_WORDS,
    max_word_count: int = 0,
    settings: Optional["GenerationSettings"] = None,
) -> list[ExpandedKeyword]:
    """
    Expand using CONSIDERATION_PATTERNS template.
    """
    modifiers = modifiers or _build_modifiers_from_settings(settings) or DEFAULT_MODIFIERS
    patterns = patterns or CONSIDERATION_PATTERNS
    locations = modifiers.get("location", ["south africa"])
    attributes = modifiers.get("attributes", [])[:3]
    colors = modifiers.get("colors", [])[:3]
    min_w = min_word_count
    max_w = max_word_count or 999
    kw_types = (settings.keyword_types if settings else None) or ["location_based", "product_attribute", "intent_modifier"]

    seen = set()
    results = []

    for product in product_terms:
        product_norm = _normalize_keyword(product)
        if not product_norm:
            continue

        for pattern in patterns:
            try:
                # Simple pattern substitution
                kw = pattern.replace("{product}", product_norm)
                if "{location}" in kw and "location_based" in kw_types:
                    for loc in locations:
                        k = kw.replace("{location}", loc).strip()
                        if _is_longtail(k, min_w, max_w) and k not in seen:
                            seen.add(k)
                            results.append(ExpandedKeyword(
                                keyword=k,
                                intent="consideration" if "reviews" in k or "vs" in k or "best" in k else "conversion",
                                source_keyword=product,
                                source="programmatic_pattern",
                                priority=2,
                            ))
                elif "{attribute}" in kw and "product_attribute" in kw_types:
                    for attr in attributes:
                        k = kw.replace("{attribute}", attr).strip()
                        if _is_longtail(k, min_w, max_w) and k not in seen:
                            seen.add(k)
                            results.append(ExpandedKeyword(
                                keyword=k,
                                intent="conversion",
                                source_keyword=product,
                                source="programmatic_pattern",
                                priority=1,
                            ))
                elif "{color}" in kw and "product_attribute" in kw_types:
                    for color in colors:
                        k = kw.replace("{color}", color).strip()
                        if _is_longtail(k, min_w, max_w) and k not in seen:
                            seen.add(k)
                            results.append(ExpandedKeyword(
                                keyword=k,
                                intent="conversion",
                                source_keyword=product,
                                source="programmatic_pattern",
                                priority=1,
                            ))
                elif "{alternative}" in kw:
                    # Skip - comparison pairs need manual curation or AI
                    # (e.g. "breville vs sage" not "couch vs cutlery")
                    continue
                else:
                    if _is_longtail(kw, min_w, max_w) and kw not in seen:
                        seen.add(kw)
                        results.append(ExpandedKeyword(
                            keyword=kw,
                            intent="conversion",
                            source_keyword=product,
                            source="programmatic_pattern",
                            priority=1,
                        ))
            except (KeyError, ValueError):
                continue

    return results


def run_programmatic_expansion(
    sources: list[KeywordSource],
    max_keywords: int = 10000,
    modifiers: dict = None,
    settings: Optional[GenerationSettings] = None,
) -> list[ExpandedKeyword]:
    """
    Full programmatic expansion pipeline.
    Takes keyword sources and generates thousands of long-tail variations.
    """
    min_w = (settings.min_words if settings else LONGTAIL_MIN_WORDS)
    max_w = (settings.max_words if settings else 0) or 999

    # Collect seed keywords
    seed_keywords = list({_normalize_keyword(s.keyword) for s in sources if s.keyword})
    product_terms = list({_extract_core_product(s.keyword) for s in sources if s.keyword})
    product_terms = [p for p in product_terms if len(p.split()) >= 1]

    # Add high-performing queries as seeds (from Search Console)
    for s in sources:
        if s.source == "search_console" and s.impressions >= 10:
            seed_keywords.append(_normalize_keyword(s.keyword))

    seed_keywords = list(dict.fromkeys(seed_keywords))[:500]  # Limit seeds
    product_terms = list(dict.fromkeys(product_terms))[:200]

    all_expanded = []

    # 1. Modifier expansion
    expanded_modifiers = expand_with_modifiers(
        seed_keywords,
        modifiers=modifiers,
        max_per_seed=30,
        min_word_count=min_w,
        max_word_count=max_w,
        settings=settings,
    )
    all_expanded.extend(expanded_modifiers)

    # 2. Pattern expansion
    expanded_patterns = expand_from_patterns(
        product_terms,
        modifiers=modifiers,
        min_word_count=min_w,
        max_word_count=max_w,
        settings=settings,
    )
    all_expanded.extend(expanded_patterns)

    # 3. Add original high-value queries as-is (with metadata)
    for s in sources:
        kw = _normalize_keyword(s.keyword)
        if _is_longtail(kw, min_w, max_w) and kw not in {e.keyword for e in all_expanded}:
            priority = 3 if s.clicks > 0 or s.impressions > 100 else 1
            all_expanded.append(ExpandedKeyword(
                keyword=kw,
                intent="conversion",
                source_keyword=s.keyword,
                source=s.source,
                product_url=s.product_url,
                seo_title=s.seo_title,
                priority=priority,
            ))

    # Filter by selected intents
    if settings and settings.intents:
        all_expanded = [e for e in all_expanded if e.intent in settings.intents]

    # Deduplicate by keyword, keep highest priority
    by_kw = {}
    for e in all_expanded:
        k = _normalize_keyword(e.keyword)
        if k not in by_kw or e.priority > by_kw[k].priority:
            by_kw[k] = e

    result = sorted(by_kw.values(), key=lambda x: (-x.priority, x.keyword))[:max_keywords]
    return result
