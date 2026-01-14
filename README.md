# 🧬 Clinical Trials Analytics Dashboard (API vs Playwright)

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-app-orange.svg)](https://streamlit.io/)

A portfolio-ready dashboard that compares **two real-world data acquisition pipelines** for ClinicalTrials.gov:

- **Official API pipeline** (fast, structured)
- **Browser automation pipeline (Playwright)** (slower, but works on dynamic/JS-rendered pages)

This is an **Upwork sample portfolio project** for **Balazs Csigi**.

---

## Selling points (skills demonstrated)

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

---

## Run live (Streamlit Community Cloud)

### Option A (simple): API-only demo

This is the easiest and most reliable “live” setup.

1. Push this repo to GitHub
2. Create a new app in Streamlit Community Cloud
3. Set the entrypoint to `app.py`
4. Use **Fetch from Official API** inside the app

### Option B (advanced): Enable Playwright in the cloud

Playwright needs browser binaries + OS-level dependencies. On Streamlit Community Cloud you typically:

- Add a `postBuild` script that runs: `python -m playwright install chromium`
- Add a `packages.txt` for required system libraries

This repo includes both at the repo root:

- `packages.txt` (apt packages installed during build)
- `postBuild` (installs Playwright Chromium via `python -m playwright install chromium`)

Deployment steps:

1. Push the repo to GitHub (make sure `packages.txt` and `postBuild` are committed)
2. In Streamlit Community Cloud, create the app from your repo
3. Set the entrypoint to `app.py`
4. Wait for the build to finish (the Playwright browser install runs during build)
5. In the running app, you can use **Run Browser Scraper (Playwright)**

If the build fails due to missing system libraries, Streamlit Cloud will show the apt error in build logs—add the missing package name to `packages.txt` and redeploy.

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


