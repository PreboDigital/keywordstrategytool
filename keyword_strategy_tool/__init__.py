"""
Keyword Strategy Tool
Generates thousands of high-intent consideration keywords for Straider.ai programmatic SEO.
"""

from .config import DEFAULT_MODIFIERS, STRAIDER_EXPORT_COLUMNS
from .data_loaders import (
    load_search_console_queries,
    load_product_pages,
    load_google_ads_search_terms,
    product_pages_to_keyword_sources,
    search_console_to_keyword_sources,
    KeywordSource,
    ProductPage,
    SearchConsoleQuery,
)
from .programmatic_expander import (
    run_programmatic_expansion,
    ExpandedKeyword,
    GenerationSettings,
)
from .ai_expander import (
    analyze_patterns_with_ai,
    generate_keywords_with_ai,
    generate_keywords_ai_only,
)

__all__ = [
    "GenerationSettings",
    "load_search_console_queries",
    "load_product_pages",
    "load_google_ads_search_terms",
    "product_pages_to_keyword_sources",
    "search_console_to_keyword_sources",
    "run_programmatic_expansion",
    "analyze_patterns_with_ai",
    "generate_keywords_with_ai",
    "generate_keywords_ai_only",
    "ExpandedKeyword",
    "KeywordSource",
    "ProductPage",
    "SearchConsoleQuery",
    "DEFAULT_MODIFIERS",
    "STRAIDER_EXPORT_COLUMNS",
]
