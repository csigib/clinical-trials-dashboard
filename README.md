# 🧬 Clinical Trials Analytics Dashboard (API vs Playwright)

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-app-orange.svg)](https://streamlit.io/)

A portfolio-ready dashboard that compares **two real-world data acquisition pipelines** for ClinicalTrials.gov:

- **Official API pipeline** (fast, structured)
- **Browser automation pipeline (Playwright)** (slower, but works on dynamic/JS-rendered pages)

This is a **Portfolio project** for **Balazs Csigi**.

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

IMPORTANT: If you see the message "This app has gone to sleep due to inactivity", just press the button "Yes, get this app back up!" and the app should load within a few seconds. If it still doesn't load, just refresh the browser.

---

## Notes

- **Playwright is expected to be slower than the API** here. That’s intentional: it demonstrates browser automation and robustness on dynamic pages.
- Scraping should be done responsibly and in accordance with site terms.

---





