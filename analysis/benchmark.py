import time
import streamlit as st
from analysis.api_client import fetch_trials
from analysis.playwright_scraper import scrape_trials

def benchmark_api(disease):
    """Live API benchmark"""
    start = time.time()
    _ = fetch_trials(disease)
    return round(time.time() - start, 2)

def benchmark_scraper_simulated():
    """Simulated scraper benchmark (fast demo)"""
    return round(15 + (5 * time.time() % 1), 2)  # random-ish placeholder

def benchmark_scraper_live(disease, max_results=100):
    """Live scraper benchmark with progress"""
    st.info("⚠️ Scraper benchmark: this may take 1–3 minutes due to throttling")
    progress = st.progress(0)
    start_time = time.time()
    df = scrape_trials(disease, max_results=max_results)
    elapsed = round(time.time() - start_time, 2)
    progress.progress(100)
    st.success(f"Scraper fetched {len(df)} trials in {elapsed} seconds")
    return elapsed
