#!/usr/bin/env python3
"""
Keyword Strategy Tool - Web UI
Run with: streamlit run app.py
"""

import os
import tempfile
import threading
import time
import uuid
from pathlib import Path

import streamlit as st

sys_path = Path(__file__).parent
if str(sys_path) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path))

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
from keyword_strategy_tool.config import DEFAULT_LOCATIONS, INTENT_TYPES, KEYWORD_TYPES
from keyword_strategy_tool.export import export_to_straider_csv

# Job store for background generation (in-memory, per process)
if "jobs" not in st.session_state:
    st.session_state.jobs = {}

st.set_page_config(page_title="Keyword Strategy Tool", page_icon="🔑", layout="wide")

st.title("🔑 Keyword Strategy Tool")
st.caption("Generate high-intent long-tail keywords for Straider.ai")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload data")
    search_console_file = st.file_uploader(
        "Search Console queries CSV",
        type=["csv"],
        help="Columns: Top queries, Clicks, Impressions, CTR, Position",
    )
    product_pages_file = st.file_uploader(
        "Product pages CSV",
        type=["csv"],
        help="Columns: Top pages, SEO Title, SEO Description, Clicks, Impressions",
    )
    google_ads_file = st.file_uploader(
        "Google Ads search terms (optional)",
        type=["csv"],
    )

with col2:
    st.subheader("Generation settings")

    # Intent
    intents = st.multiselect(
        "Intent types",
        options=["educational", "consideration", "conversion"],
        default=["educational", "consideration", "conversion"],
        help="Educational: how-to, guides. Consideration: reviews, vs, best. Conversion: for sale, price, deals.",
    )

    # Keyword types
    keyword_types = st.multiselect(
        "Keyword types",
        options=KEYWORD_TYPES,
        default=KEYWORD_TYPES,
        help="Location-based: product + location. Product attribute: color, size. Intent modifier: reviews, price, etc.",
    )

    # Locations
    st.write("**Locations**")
    loc_col1, loc_col2 = st.columns(2)
    with loc_col1:
        default_locs = st.multiselect(
            "Preset locations",
            options=DEFAULT_LOCATIONS,
            default=DEFAULT_LOCATIONS[:3],
            key="preset_locs",
        )
    with loc_col2:
        custom_loc = st.text_input(
            "Add custom location",
            placeholder="e.g. port elizabeth",
            key="custom_loc",
        )
    locations = list(default_locs)
    if custom_loc and custom_loc.strip():
        locations.append(custom_loc.strip().lower())

    # Keyword length
    len_col1, len_col2 = st.columns(2)
    with len_col1:
        min_words = st.number_input("Min words", min_value=2, max_value=10, value=3, key="min_words")
    with len_col2:
        max_words = st.number_input("Max words (0 = no limit)", min_value=0, max_value=15, value=0, key="max_words")

    st.subheader("Options")
    max_keywords = st.number_input("Max keywords", min_value=100, max_value=50000, value=5000, step=500)
    use_ai = st.checkbox(
        "Use AI expansion (recommended - unique angles)",
        value=bool(os.environ.get("OPENAI_API_KEY")),
        help="Uses AI to generate distinct search-intent keywords. Requires OPENAI_API_KEY.",
    )
    brand = st.text_input("Brand name (for AI context)", placeholder="e.g. Bash")
    run_in_background = st.checkbox(
        "Run in background (for large jobs, avoids timeout)",
        value=False,
        help="Recommended for Railway or when generating 10k+ keywords",
    )


def run_generation(
    sc_bytes,
    pp_bytes,
    ga_bytes,
    settings: GenerationSettings,
    max_keywords: int,
    use_ai: bool,
    brand: str,
    job_id: str,
):
    """Run keyword generation (for background thread)."""
    try:
        st.session_state.jobs[job_id]["status"] = "loading"
        sources = []

        if sc_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                f.write(sc_bytes)
                f.flush()
                queries = load_search_console_queries(f.name)
                sources.extend(search_console_to_keyword_sources(queries))
                os.unlink(f.name)

        if pp_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                f.write(pp_bytes)
                f.flush()
                pages = load_product_pages(f.name)
                sources.extend(product_pages_to_keyword_sources(pages))
                os.unlink(f.name)

        if ga_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                f.write(ga_bytes)
                f.flush()
                ads = load_google_ads_search_terms(f.name)
                sources.extend(ads)
                os.unlink(f.name)

        st.session_state.jobs[job_id]["status"] = "expanding"
        expanded = run_programmatic_expansion(sources, max_keywords=max_keywords, settings=settings)

        if use_ai and os.environ.get("OPENAI_API_KEY"):
            from keyword_strategy_tool.programmatic_expander import _angle_key
            existing_angles = {_angle_key(e.keyword) for e in expanded}
            sample = [s.keyword for s in sources if s.source == "search_console"][:50]
            ai_result = analyze_patterns_with_ai(sample, brand_name=brand or "Bash")
            if ai_result:
                for kw in ai_result.keywords:
                    if kw not in {e.keyword for e in expanded} and _angle_key(kw) not in existing_angles:
                        expanded.append(ExpandedKeyword(
                            keyword=kw, intent="consideration",
                            source_keyword="ai", source="ai",
                            product_url=None, seo_title=None, priority=4,
                        ))
                        existing_angles.add(_angle_key(kw))
            # Per-product AI (top 5 pages)
            if pp_bytes:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                    f.write(pp_bytes)
                    f.flush()
                    pages = load_product_pages(f.name)
                    os.unlink(f.name)
                for page in pages[:5]:
                    ai_kws = generate_keywords_with_ai(
                        product_url=page.url,
                        seo_title=page.seo_title,
                        seo_description=page.seo_description,
                        existing_queries=[s.keyword for s in sources][:30],
                        brand_name=brand,
                        num_keywords=25,
                    )
                    for ai_kw in ai_kws:
                        if ai_kw.keyword not in {e.keyword for e in expanded} and _angle_key(ai_kw.keyword) not in existing_angles:
                            ai_kw.source = "ai"
                            ai_kw.priority = 4
                            expanded.append(ai_kw)
                            existing_angles.add(_angle_key(ai_kw.keyword))

        seen = set()
        unique = []
        for e in expanded:
            k = e.keyword.lower().strip()
            if k not in seen:
                seen.add(k)
                unique.append(e)
        unique.sort(key=lambda x: (-x.priority, x.keyword))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            export_to_straider_csv(unique, f.name)
            csv_data = Path(f.name).read_text()
            os.unlink(f.name)

        st.session_state.jobs[job_id]["status"] = "done"
        st.session_state.jobs[job_id]["result"] = unique
        st.session_state.jobs[job_id]["csv_data"] = csv_data
    except Exception as e:
        st.session_state.jobs[job_id]["status"] = "error"
        st.session_state.jobs[job_id]["error"] = str(e)


if st.button("Generate keywords", type="primary"):
    if not search_console_file and not product_pages_file:
        st.error("Upload at least Search Console or Product Pages CSV")
    else:
        settings = GenerationSettings(
            intents=intents or ["educational", "consideration", "conversion"],
            keyword_types=keyword_types or KEYWORD_TYPES,
            locations=locations or DEFAULT_LOCATIONS[:3],
            min_words=min_words,
            max_words=max_words if max_words > 0 else 0,
        )

        if run_in_background:
            job_id = str(uuid.uuid4())[:8]
            st.session_state.jobs[job_id] = {"status": "pending", "result": None, "csv_data": None, "error": None}

            # Store file bytes for thread (Streamlit uploaders are not thread-safe)
            sc_bytes = search_console_file.getvalue() if search_console_file else None
            pp_bytes = product_pages_file.getvalue() if product_pages_file else None
            ga_bytes = google_ads_file.getvalue() if google_ads_file else None

            def run():
                run_generation(sc_bytes, pp_bytes, ga_bytes, settings, max_keywords, use_ai, brand, job_id)

            thread = threading.Thread(target=run)
            thread.start()

            st.success(f"Generation started in background. Job ID: **{job_id}**")
            st.info("Refresh the page in a few seconds to check status. Results will appear below.")
            st.session_state.current_job_id = job_id
        else:
            # Synchronous generation
            sources = []
            with st.spinner("Loading data..."):
                if search_console_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                        f.write(search_console_file.getvalue())
                        queries = load_search_console_queries(f.name)
                        sources.extend(search_console_to_keyword_sources(queries))
                        os.unlink(f.name)
                    st.success(f"Loaded {len(queries)} Search Console queries")

                if product_pages_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                        f.write(product_pages_file.getvalue())
                        pages = load_product_pages(f.name)
                        sources.extend(product_pages_to_keyword_sources(pages))
                        os.unlink(f.name)
                    st.success(f"Loaded {len(pages)} product pages")

                if google_ads_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                        f.write(google_ads_file.getvalue())
                        ads = load_google_ads_search_terms(f.name)
                        sources.extend(ads)
                        os.unlink(f.name)
                    st.success(f"Loaded {len(ads)} Google Ads terms")

            if sources:
                with st.spinner("Expanding keywords..."):
                    expanded = run_programmatic_expansion(sources, max_keywords=max_keywords, settings=settings)

                    if use_ai and os.environ.get("OPENAI_API_KEY"):
                        with st.spinner("AI expansion (unique angles)..."):
                            from keyword_strategy_tool.programmatic_expander import _angle_key
                            sample = [s.keyword for s in sources if s.source == "search_console"][:50]
                            ai_result = analyze_patterns_with_ai(sample, brand_name=brand or "Bash")
                            existing_angles = {_angle_key(e.keyword) for e in expanded}
                            if ai_result:
                                for kw in ai_result.keywords:
                                    if kw not in {e.keyword for e in expanded} and _angle_key(kw) not in existing_angles:
                                        expanded.append(ExpandedKeyword(
                                            keyword=kw, intent="consideration",
                                            source_keyword="ai", source="ai",
                                            product_url=None, seo_title=None, priority=4,
                                        ))
                                        existing_angles.add(_angle_key(kw))

                    seen = set()
                    unique = []
                    for e in expanded:
                        k = e.keyword.lower().strip()
                        if k not in seen:
                            seen.add(k)
                            unique.append(e)
                    unique.sort(key=lambda x: (-x.priority, x.keyword))

                st.success(f"Generated **{len(unique)}** keywords")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                    export_to_straider_csv(unique, f.name)
                    csv_data = Path(f.name).read_text()
                    os.unlink(f.name)

                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name="keywords_straider_export.csv",
                    mime="text/csv",
                )

                st.subheader("Preview")
                import pandas as pd
                df = pd.DataFrame([{"keyword": e.keyword, "intent": e.intent, "priority": e.priority} for e in unique[:100]])
                st.dataframe(df, use_container_width=True, height=400)

# Background job status
if st.session_state.jobs:
    st.divider()
    st.subheader("Background jobs")
    for jid, job in list(st.session_state.jobs.items()):
        with st.expander(f"Job {jid}: {job['status']}", expanded=job["status"] == "done"):
            if job["status"] == "done":
                st.success("Completed!")
                if job.get("result"):
                    st.download_button(
                        f"Download CSV ({len(job['result'])} keywords)",
                        data=job.get("csv_data", ""),
                        file_name=f"keywords_{jid}.csv",
                        mime="text/csv",
                        key=f"dl_{jid}",
                    )
                    import pandas as pd
                    df = pd.DataFrame([{"keyword": e.keyword, "intent": e.intent} for e in job["result"][:50]])
                    st.dataframe(df, use_container_width=True)
            elif job["status"] == "error":
                st.error(job.get("error", "Unknown error"))
            else:
                st.info("In progress... Refresh to check status.")
