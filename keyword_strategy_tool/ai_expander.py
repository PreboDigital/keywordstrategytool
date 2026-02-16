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

Here are real search queries from Google Search Console (high-intent, consideration stage):
{json.dumps(sample, indent=2)}

Analyze these queries and identify:
1. COMMON PATTERNS: What structures repeat? (e.g., "brand + product + location", "product + for sale + location")
2. INTENT SIGNALS: What words indicate buying intent vs research? (reviews, vs, best, price, deals)
3. 10 NEW LONG-TAIL KEYWORDS: Generate 10 high-intent consideration keywords (3+ words each) that follow the same patterns but weren't in the list. Focus on commercial and consideration intent.

Respond in JSON only:
{{
  "patterns": ["pattern 1", "pattern 2", ...],
  "intent_signals": {{"commercial": [...], "consideration": [...]}},
  "new_keywords": ["keyword 1", "keyword 2", ...],
  "reasoning": "Brief explanation of patterns found"
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
        return AIPatternResult(
            pattern_type="ai_analysis",
            keywords=data.get("new_keywords", []),
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

    prompt = f"""You are an SEO strategist for Straider.ai's programmatic SEO platform. Generate high-intent CONSIDERATION and COMMERCIAL long-tail keywords for content that will rank and drive sales.

PRODUCT PAGE:
- URL: {product_url}
- SEO Title: {seo_title}
- SEO Description: {seo_description}

EXISTING SEARCH QUERIES (from Search Console - what people already search):
{json.dumps(existing, indent=2)}

Generate {num_keywords} NEW long-tail keywords (3-6 words each) that:
1. Follow the same patterns as existing queries
2. Target consideration stage (reviews, vs, best, comparison, guide)
3. Include location "south africa" where relevant
4. Would attract buyers researching before purchase
5. Are NOT duplicates of existing queries

Return ONLY a JSON array of keyword strings, no explanation:
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
