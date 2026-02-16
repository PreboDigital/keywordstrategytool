"""
Keyword Strategy Tool - AI-Powered Keyword Expansion
Uses LLM to discover patterns and generate high-intent consideration keywords.
Optional: requires OPENAI_API_KEY. Falls back to programmatic-only if not set.
"""

import os
import json
from typing import Optional
from dataclasses import dataclass

from .programmatic_expander import ExpandedKeyword


@dataclass
class AIPatternResult:
    """Pattern or keyword suggestion from AI."""
    pattern_type: str
    keywords: list[str]
    reasoning: str


def _get_openai_client():
    """Lazy load OpenAI to avoid import errors when not used."""
    try:
        import openai
        return openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except ImportError:
        return None


def analyze_patterns_with_ai(
    sample_queries: list[str],
    product_context: str = "",
    brand_name: str = "",
) -> Optional[AIPatternResult]:
    """
    Use AI to analyze search query patterns and suggest new keyword patterns.
    Returns None if OpenAI not configured.
    """
    client = _get_openai_client()
    if not client or not os.environ.get("OPENAI_API_KEY"):
        return None

    sample = sample_queries[:50]  # Limit tokens
    prompt = f"""You are an SEO expert analyzing search behavior for an eCommerce/retail brand.

Brand: {brand_name or "Generic"}
Product context: {product_context or "Home goods, furniture, appliances"}

Here are real search queries from Google Search Console:
{json.dumps(sample, indent=2)}

Generate 15 UNIQUE ANGLE keywords - each must represent a DISTINCT search intent. No near-duplicates.
- One angle = one searcher need (e.g. "reviews" vs "best" vs "price" are different angles)
- Include: consideration (reviews, vs, best, comparison), conversion (for sale, price, buy), educational (how to, guide)
- Add "south africa" where relevant for local SEO
- Each keyword must be 3-6 words and NOT in the existing list
- Avoid redundant variations (e.g. don't give both "X south africa" and "X in south africa")

Respond in JSON only:
{{
  "patterns": ["pattern 1", "pattern 2"],
  "new_keywords": ["keyword 1", "keyword 2", ...],
  "reasoning": "Brief explanation of unique angles identified"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        # Extract JSON (handle markdown code blocks)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        keywords = data.get("new_keywords", [])
        # Dedupe and ensure 3+ words
        keywords = list(dict.fromkeys(k for k in keywords if isinstance(k, str) and len(k.split()) >= 3))
        return AIPatternResult(
            pattern_type="ai_analysis",
            keywords=keywords,
            reasoning=data.get("reasoning", ""),
        )
    except Exception:
        return None


def generate_keywords_with_ai(
    product_url: str,
    seo_title: str,
    seo_description: str,
    existing_queries: list[str],
    brand_name: str = "",
    num_keywords: int = 50,
) -> list[ExpandedKeyword]:
    """
    Generate long-tail consideration keywords using AI based on product page + search data.
    Returns empty list if OpenAI not configured.
    """
    client = _get_openai_client()
    if not client or not os.environ.get("OPENAI_API_KEY"):
        return []

    existing = existing_queries[:30]

    prompt = f"""You are an SEO strategist for Straider.ai. Generate UNIQUE ANGLE keywords - each must represent a DISTINCT search intent.

PRODUCT: {seo_title}
URL: {product_url}
Description: {seo_description[:200]}...

EXISTING QUERIES (do not duplicate):
{json.dumps(existing[:25], indent=2)}

Generate {num_keywords} NEW keywords (3-6 words each). Rules:
- ONE keyword per unique angle (reviews vs best vs price vs for sale = different angles)
- Mix: consideration (reviews, vs, best), conversion (for sale, price, buy), educational (how to, guide)
- Add "south africa" where it fits naturally
- No near-duplicates (e.g. not both "X south africa" and "X in south africa")
- Each keyword = distinct searcher need

Return ONLY a JSON array:
["keyword 1", "keyword 2", ...]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        keywords = json.loads(content)
        if not isinstance(keywords, list):
            return []

        return [
            ExpandedKeyword(
                keyword=str(kw),
                intent="consideration",
                source_keyword=seo_title,
                source="ai_generated",
                product_url=product_url,
                seo_title=seo_title,
                priority=3,
            )
            for kw in keywords[:num_keywords]
            if isinstance(kw, str) and len(kw.split()) >= 3
        ]
    except Exception:
        return []
