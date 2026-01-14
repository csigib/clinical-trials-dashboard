# 🧬 Clinical Trials Analytics Dashboard (API vs Playwright)

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-app-orange.svg)](https://streamlit.io/)

A portfolio-ready dashboard that compares **two real-world data acquisition pipelines** for ClinicalTrials.gov:

- **Official API pipeline** (fast, structured)
- **Browser automation pipeline (Playwright)** (slower, but works on dynamic/JS-rendered pages)

This is an **Upwork sample portfolio project** for **Balazs Csigi**.

---

## Skills demonstrated

- **Data pipelines end-to-end**: ingestion → normalization → validation → analytics → visualization
- **Browser scraping on JS-heavy sites**: Playwright automation (selectors, pagination, detail extraction, fallbacks)
- **Engineering tradeoffs**: highlights speed vs robustness differences between API and browser scraping
- **Data visualization**: interactive Plotly charts + choropleth map + heatmaps
- **Practical app UX**: cached API fetches, JSONL outputs, subprocess-driven scraping, responsive tables

---

## What the app does

- Select a disease (Type 2 Diabetes, Breast Cancer, Alzheimer’s, COVID-19, Parkinson’s)
- Load trials via:
  - **ClinicalTrials.gov API** (recommended)
  - **Playwright browser scraper** (demo of browser automation for JS-intensive sites)
- Visualize:
  - Trials per year trend
  - Country distribution map (interactive choropleth)
  - Country heatmap
- Export results as CSV

---

## Run locally

### 1) Prerequisites

- Python **3.10+** (3.11 recommended)

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Install Playwright browsers (one-time)

Playwright requires browser binaries installed separately:

```bash
python -m playwright install
```

If you only want Chromium:

```bash
python -m playwright install chromium
```

### 4) Start the Streamlit app

```bash
streamlit run app.py
```

If you prefer launching Streamlit via Python (e.g., when the `streamlit` command isn’t on your PATH):

```bash
python -m streamlit run app.py
```

---

## Run live (Streamlit)

Live demo:

-  https://clinical-trials-dashboard-ghv6ndgxx3yrn2hcrfyu69.streamlit.app/

If you want to deploy your own copy on Streamlit Community Cloud, use the official guide:

- https://docs.streamlit.io/streamlit-community-cloud

---

## Playwright scraper CLI (optional)

The Streamlit app runs Playwright as a subprocess, but you can also run it directly:

```bash
python analysis/playwright_scraper.py \
  --disease "Type 2 Diabetes" \
  --max_results 25 \
  --output data/out.jsonl \
  --headless
```

Windows PowerShell example:

```powershell
python .\analysis\playwright_scraper.py --disease "Type 2 Diabetes" --max_results 25 --output .\data\out.jsonl --headless
```

The output is **JSONL** (one JSON object per line) with keys:

- `nctId`
- `briefTitle`
- `startYear`
- `country`

---

## Notes

- **Playwright is expected to be slower than the API** here. That’s intentional: it demonstrates browser automation and robustness on dynamic pages.
- Scraping should be done responsibly and in accordance with site terms.

---



