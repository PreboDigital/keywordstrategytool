"""
Keyword Strategy Tool - Data Loaders
Ingests Search Console, product pages, and Google Ads search terms.
"""

import csv
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class SearchConsoleQuery:
    """Single query from Google Search Console."""
    query: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: float = 0.0
    word_count: int = 0


@dataclass
class ProductPage:
    """Product/category page with SEO metadata."""
    url: str
    seo_title: str
    seo_description: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: float = 0.0


@dataclass
class KeywordSource:
    """Unified keyword source for processing."""
    keyword: str
    source: str  # "search_console" | "product_page" | "google_ads"
    product_url: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: float = 0.0


def load_search_console_queries(csv_path: str) -> list[SearchConsoleQuery]:
    """
    Load Search Console queries CSV.
    Expected columns: Top queries, Clicks, Impressions, CTR, Position, LEN (optional)
    """
    queries = []
    path = Path(csv_path)
    if not path.exists():
        return queries

    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query_text = row.get("Top queries", row.get("Query", row.get("query", ""))).strip()
            if not query_text:
                continue

            try:
                clicks = int(row.get("Clicks", row.get("clicks", 0)) or 0)
            except (ValueError, TypeError):
                clicks = 0
            try:
                impressions = int(row.get("Impressions", row.get("impressions", 0)) or 0)
            except (ValueError, TypeError):
                impressions = 0
            try:
                ctr_str = row.get("CTR", row.get("ctr", "0")).replace("%", "")
                ctr = float(ctr_str) if ctr_str else 0.0
            except (ValueError, TypeError):
                ctr = 0.0
            try:
                position = float(row.get("Position", row.get("position", 0)) or 0)
            except (ValueError, TypeError):
                position = 0.0

            word_count = len(query_text.split())

            queries.append(SearchConsoleQuery(
                query=query_text,
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                position=position,
                word_count=word_count,
            ))

    return queries


def load_product_pages(csv_path: str) -> list[ProductPage]:
    """
    Load product/category pages with SEO metadata.
    Expected columns: Top pages, Clicks, Impressions, CTR, Position, SEO Title, SEO Description
    """
    pages = []
    path = Path(csv_path)
    if not path.exists():
        return pages

    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Top pages", row.get("URL", row.get("url", ""))).strip()
            if not url:
                continue

            seo_title = row.get("SEO Title", row.get("seo_title", "")).strip()
            seo_description = row.get("SEO Description", row.get("seo_description", "")).strip()

            try:
                clicks = int(row.get("Clicks", 0) or 0)
            except (ValueError, TypeError):
                clicks = 0
            try:
                impressions = int(row.get("Impressions", 0) or 0)
            except (ValueError, TypeError):
                impressions = 0
            try:
                ctr_str = row.get("CTR", "0").replace("%", "")
                ctr = float(ctr_str) if ctr_str else 0.0
            except (ValueError, TypeError):
                ctr = 0.0
            try:
                position = float(row.get("Position", 0) or 0)
            except (ValueError, TypeError):
                position = 0.0

            pages.append(ProductPage(
                url=url,
                seo_title=seo_title,
                seo_description=seo_description,
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                position=position,
            ))

    return pages


def load_google_ads_search_terms(csv_path: str) -> list[KeywordSource]:
    """
    Load Google Ads search terms report.
    Expected columns: Search term, Clicks, Impressions, CTR, etc.
    """
    keywords = []
    path = Path(csv_path)
    if not path.exists():
        return keywords

    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row.get("Search term", row.get("search_term", row.get("Keyword", ""))).strip()
            if not term:
                continue

            try:
                clicks = int(row.get("Clicks", 0) or 0)
            except (ValueError, TypeError):
                clicks = 0
            try:
                impressions = int(row.get("Impressions", 0) or 0)
            except (ValueError, TypeError):
                impressions = 0

            keywords.append(KeywordSource(
                keyword=term,
                source="google_ads",
                clicks=clicks,
                impressions=impressions,
            ))

    return keywords


def extract_keywords_from_text(text: str) -> list[str]:
    """Extract meaningful keywords from SEO title/description."""
    if not text:
        return []
    # Remove HTML entities
    text = re.sub(r"&[a-z]+;|&#\d+;", " ", text)
    # Split on punctuation and whitespace
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    # Filter stopwords and short words
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "more", "most", "your", "our", "their", "its", "amp"}
    keywords = [w for w in words if len(w) > 2 and w not in stopwords]
    return keywords


def product_pages_to_keyword_sources(pages: list[ProductPage]) -> list[KeywordSource]:
    """Convert product pages to keyword sources by extracting from URL, title, description."""
    sources = []
    for page in pages:
        # Extract product/category from URL path
        url_path = page.url.split("/")[-1] if "/" in page.url else page.url
        url_keywords = url_path.replace("-", " ").replace("_", " ").split()
        url_keyword = " ".join(url_keywords) if url_keywords else ""

        # Extract from SEO title (main product phrase)
        title_keywords = extract_keywords_from_text(page.seo_title)
        title_phrase = " ".join(title_keywords[:5]) if title_keywords else ""

        # Extract from description
        desc_keywords = extract_keywords_from_text(page.seo_description)

        # Primary: use SEO title as main keyword
        if title_phrase:
            sources.append(KeywordSource(
                keyword=title_phrase,
                source="product_page",
                product_url=page.url,
                seo_title=page.seo_title,
                seo_description=page.seo_description,
                clicks=page.clicks,
                impressions=page.impressions,
                ctr=page.ctr,
                position=page.position,
            ))

        # Secondary: URL-based product term (from path)
        if url_keyword and url_keyword != title_phrase:
            sources.append(KeywordSource(
                keyword=url_keyword,
                source="product_page",
                product_url=page.url,
                seo_title=page.seo_title,
                seo_description=page.seo_description,
            ))

    return sources


def search_console_to_keyword_sources(queries: list[SearchConsoleQuery]) -> list[KeywordSource]:
    """Convert Search Console queries to keyword sources."""
    return [
        KeywordSource(
            keyword=q.query,
            source="search_console",
            clicks=q.clicks,
            impressions=q.impressions,
            ctr=q.ctr,
            position=q.position,
        )
        for q in queries
    ]
