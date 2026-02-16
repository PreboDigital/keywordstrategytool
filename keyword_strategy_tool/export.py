"""
Keyword Strategy Tool - Export for Straider.ai
Exports keywords in Straider-ready CSV format.
"""

import csv
from pathlib import Path
from typing import Optional

from .programmatic_expander import ExpandedKeyword


def export_to_straider_csv(
    keywords: list[ExpandedKeyword],
    output_path: str,
    include_metadata: bool = True,
) -> str:
    """
    Export expanded keywords to CSV for Straider.ai content generation.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    columns = ["keyword", "intent", "source", "priority"]
    if include_metadata:
        columns.extend(["product_url", "seo_title", "source_keyword"])

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for kw in keywords:
            row = {
                "keyword": kw.keyword,
                "intent": kw.intent,
                "source": kw.source,
                "priority": kw.priority,
                "product_url": kw.product_url or "",
                "seo_title": kw.seo_title or "",
                "source_keyword": kw.source_keyword,
            }
            writer.writerow(row)

    return str(path.absolute())
