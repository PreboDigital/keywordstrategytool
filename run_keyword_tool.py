#!/usr/bin/env python3
"""
Keyword Strategy Tool - CLI Runner
Generates thousands of high-intent long-tail keywords from:
- Product URLs + SEO titles + descriptions
- Search Console queries
- Google Ads search terms (optional)

Designed for Straider.ai programmatic SEO - drives organic traffic that converts.
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from keyword_strategy_tool import (
    load_search_console_queries,
    load_product_pages,
    load_google_ads_search_terms,
    product_pages_to_keyword_sources,
    search_console_to_keyword_sources,
    run_programmatic_expansion,
    generate_keywords_with_ai,
    analyze_patterns_with_ai,
    ExpandedKeyword,
    GenerationSettings,
)
from keyword_strategy_tool.programmatic_expander import _angle_key
from keyword_strategy_tool.export import export_to_straider_csv


def main():
    parser = argparse.ArgumentParser(
        description="Keyword Strategy Tool - Generate high-intent long-tail keywords for Straider.ai"
    )
    parser.add_argument(
        "--search-console",
        "-s",
        help="Path to Search Console queries CSV",
        default=None,
    )
    parser.add_argument(
        "--product-pages",
        "-p",
        help="Path to product/category pages CSV (with SEO Title, SEO Description)",
        default=None,
    )
    parser.add_argument(
        "--google-ads",
        "-g",
        help="Path to Google Ads search terms CSV (optional)",
        default=None,
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output CSV path for Straider-ready keywords",
        default="keywords_straider_export.csv",
    )
    parser.add_argument(
        "--max-keywords",
        "-m",
        type=int,
        help="Maximum keywords to generate (default: 10000)",
        default=10000,
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Use AI to generate additional keywords (requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--brand",
        help="Brand name for AI context (e.g., Bash)",
        default="",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Print keywords to stdout only, don't write CSV",
    )

    args = parser.parse_args()

    # Require at least one input
    if not args.search_console and not args.product_pages:
        parser.error("Provide at least --search-console or --product-pages")

    sources = []

    # Load Search Console
    if args.search_console:
        queries = load_search_console_queries(args.search_console)
        sc_sources = search_console_to_keyword_sources(queries)
        sources.extend(sc_sources)
        print(f"Loaded {len(queries)} Search Console queries")

    # Load product pages
    if args.product_pages:
        pages = load_product_pages(args.product_pages)
        pp_sources = product_pages_to_keyword_sources(pages)
        sources.extend(pp_sources)
        print(f"Loaded {len(pages)} product pages")

    # Load Google Ads (optional)
    if args.google_ads:
        ads_sources = load_google_ads_search_terms(args.google_ads)
        sources.extend(ads_sources)
        print(f"Loaded {len(ads_sources)} Google Ads search terms")

    if not sources:
        print("No keyword sources loaded. Exiting.")
        sys.exit(1)

    # Programmatic expansion (unique angles only)
    settings = GenerationSettings()
    print("Running programmatic expansion...")
    expanded = run_programmatic_expansion(sources, max_keywords=args.max_keywords, settings=settings)
    print(f"Generated {len(expanded)} keywords (programmatic)")

    # AI expansion (optional) - unique angles, prioritised
    if args.use_ai and os.environ.get("OPENAI_API_KEY"):
        print("Running AI expansion (unique angles)...")
        existing_angles = {_angle_key(e.keyword) for e in expanded}
        sample_queries = [s.keyword for s in sources if s.source == "search_console"][:50]
        ai_pattern = analyze_patterns_with_ai(
            sample_queries,
            product_context="Home goods, furniture, appliances, bedding, decor",
            brand_name=args.brand or "Bash",
        )
        if ai_pattern:
            print(f"AI: {ai_pattern.reasoning[:80]}...")
            for kw in ai_pattern.keywords:
                if kw not in {e.keyword for e in expanded} and _angle_key(kw) not in existing_angles:
                    expanded.append(ExpandedKeyword(
                        keyword=kw, intent="consideration",
                        source_keyword="ai", source="ai",
                        product_url=None, seo_title=None, priority=4,
                    ))
                    existing_angles.add(_angle_key(kw))

        # Per-product AI (top 5 pages)
        if args.product_pages:
            pages = load_product_pages(args.product_pages)
            for page in pages[:5]:
                ai_kws = generate_keywords_with_ai(
                    product_url=page.url,
                    seo_title=page.seo_title,
                    seo_description=page.seo_description,
                    existing_queries=[s.keyword for s in sources][:30],
                    brand_name=args.brand,
                    num_keywords=25,
                )
                for ai_kw in ai_kws:
                    if ai_kw.keyword not in {e.keyword for e in expanded} and _angle_key(ai_kw.keyword) not in existing_angles:
                        ai_kw.source = "ai"
                        ai_kw.priority = 4
                        expanded.append(ai_kw)
                        existing_angles.add(_angle_key(ai_kw.keyword))

        print(f"Total after AI: {len(expanded)} keywords")
    elif args.use_ai and not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Skipping AI expansion.")

    # Deduplicate by keyword
    seen = set()
    unique = []
    for e in expanded:
        k = e.keyword.lower().strip()
        if k not in seen:
            seen.add(k)
            unique.append(e)

    # Sort by priority
    unique.sort(key=lambda x: (-x.priority, x.keyword))

    # Export
    if not args.no_export:
        out_path = export_to_straider_csv(unique, args.output)
        print(f"Exported {len(unique)} keywords to {out_path}")

    # Preview
    print("\n--- Sample keywords (top 20 by priority) ---")
    for e in unique[:20]:
        print(f"  [{e.intent}] {e.keyword}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
