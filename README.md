# Keyword Strategy Tool

Generates **thousands of high-intent consideration keywords** for [Straider.ai](https://straider.ai) programmatic SEO. Built to drive organic traffic that converts to sales.

## Purpose

- **Input**: Product URLs, SEO titles, descriptions, Search Console queries, Google Ads search terms
- **Output**: Long-tail keywords (3+ words) ready for Straider content generation
- **Approach**: Programmatic expansion + optional AI pattern analysis

## Quick Start

### Web UI (recommended for testing)

```bash
# From project directory
chmod +x start_server.sh
./start_server.sh
```

Then open **http://localhost:8501** in your browser. Upload your CSV files and click "Generate keywords".

### CLI – Programmatic only (no API key)

```bash
# Using Bash.com example data
python run_keyword_tool.py \
  --search-console "bash.com-Keyword Harvesting & Performance Data - quries-search-console-home-category-triggers.csv" \
  --product-pages "bash.com-Keyword Harvesting & Performance Data - Export Ready - Home Category.csv" \
  --output bash_keywords_straider.csv
```

### With AI expansion (requires OPENAI_API_KEY)

```bash
export OPENAI_API_KEY=your_key
pip install openai

python run_keyword_tool.py \
  --search-console "bash.com-Keyword Harvesting & Performance Data - quries-search-console-home-category-triggers.csv" \
  --product-pages "bash.com-Keyword Harvesting & Performance Data - Export Ready - Home Category.csv" \
  --use-ai \
  --brand Bash \
  --output bash_keywords_straider.csv
```

### With Google Ads search terms

```bash
python run_keyword_tool.py \
  --search-console queries.csv \
  --product-pages pages.csv \
  --google-ads "Google Ads - Search terms report.csv" \
  --output keywords.csv
```

## Data Formats

### Search Console CSV
- Columns: `Top queries`, `Clicks`, `Impressions`, `CTR`, `Position`, `LEN` (optional)

### Product Pages CSV
- Columns: `Top pages`, `Clicks`, `Impressions`, `CTR`, `Position`, `SEO Title`, `SEO Description`

### Google Ads Search Terms
- Columns: `Search term`, `Clicks`, `Impressions`

## How It Works

1. **Data ingestion**: Loads queries and product metadata from CSVs
2. **Programmatic expansion**:
   - Location modifiers (south africa, cape town, etc.)
   - Intent modifiers (for sale, price, reviews, deals, black friday)
   - Attribute modifiers (colors, sizes)
   - Pattern templates (e.g. `{product} reviews {location}`)
3. **AI expansion** (optional): Uses GPT to discover patterns and generate new long-tail variations
4. **Export**: Straider-ready CSV with keyword, intent, source, priority

## Straider.ai Integration

The export CSV includes:
- `keyword` – Long-tail phrase for content
- `intent` – commercial | consideration
- `source` – search_console | product_page | programmatic | ai_generated
- `priority` – 1–3 (higher = more valuable)
- `product_url` – Target page for content
- `seo_title` – Context for content generation

Use this file to feed Straider’s real-time keyword fetch and page generation.

## Customization

Edit `keyword_strategy_tool/config.py` to:
- Add location modifiers for your market
- Add intent modifiers (deals, seasonal, etc.)
- Add new pattern templates
- Adjust long-tail minimum word count

## Deploy to Railway

1. Push to GitHub: https://github.com/PreboDigital/keywordstrategytool
2. In Railway: New Project → Deploy from GitHub repo
3. Add env var `OPENAI_API_KEY` (optional, for AI expansion)
4. Deploy – Railway auto-detects Streamlit

The app uses `Procfile` and `railway.json` for deployment. For long-running jobs, enable **Run in background** to avoid request timeouts.

## License

Internal use – Prebo Digital / Straider.ai
