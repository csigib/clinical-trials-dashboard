import streamlit as st
import pandas as pd
import time
from pathlib import Path
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

from analysis.api_client import get_clinical_trials
from analysis.trend import compute_trend
from analysis.geo import country_counts, canonicalize_country
from analysis.playwright_runner import run_playwright_subprocess

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Clinical Trials Analytics", layout="wide")
st.markdown(
        """
<style>
.hero {
    padding: 1.1rem 1.2rem;
    border-radius: 14px;
    border: 1px solid rgba(20, 80, 140, 0.22);
    background: linear-gradient(135deg, rgba(20, 80, 140, 0.12), rgba(140, 50, 120, 0.08));
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.15;
    margin: 0;
}
.hero-sub {
    margin-top: 0.35rem;
    font-size: 1.05rem;
    font-weight: 650;
    opacity: 0.95;
}
.hero-meta {
    margin-top: 0.35rem;
    font-size: 0.95rem;
    opacity: 0.85;
}
</style>

<div class="hero">
    <div class="hero-title">🧬 Clinical Trials Analytics Dashboard</div>
    <div class="hero-sub">Upwork sample portfolio project for Balazs Csigi</div>
    <div class="hero-meta">API vs Browser Scraper (ClinicalTrials.gov)</div>
</div>
""",
        unsafe_allow_html=True,
)

st.write("")

# Responsive tweaks (reduce horizontal scrolling in tables).
st.markdown(
        """
<style>
div[data-testid="stDataFrame"] div[role="gridcell"],
div[data-testid="stDataFrame"] div[role="columnheader"] {
    white-space: normal !important;
}
div[data-testid="stDataFrame"] div[role="gridcell"] > div {
    white-space: normal !important;
}
@media (max-width: 768px) {
    div[data-testid="stDataFrame"] { font-size: 12px; }
}
</style>
        """,
        unsafe_allow_html=True,
)

# ---------------- Sidebar ----------------
st.sidebar.header("Configuration")
disease = st.sidebar.selectbox(
    "Select disease",
    ["Type 2 Diabetes", "Breast Cancer", "Alzheimer's Disease", "COVID-19", "Parkinson's Disease"]
)
max_results_api = st.sidebar.slider("Max results", 10, 500, 100, 10)
fetch_api_btn = st.sidebar.button("Fetch from Official API")
max_results_browser = st.sidebar.slider("Max results", 10, 30, 10, 5)
run_browser_btn = st.sidebar.button("Run Browser Scraper (Playwright)")
# Hide noisy Playwright logs by default (can be enabled for debugging).
show_playwright_logs = st.sidebar.checkbox("Show Playwright debug logs", value=False)
# uploaded_file = st.sidebar.file_uploader("Or upload pre-scraped JSONL/CSV", type=["csv", "jsonl", "json"])

# cached API fetch
@st.cache_data(ttl=300)
def fetch_api_cached(disease: str, max_results_api: int):
    t0 = time.perf_counter()
    df = get_clinical_trials(disease, page_size=max_results_api)
    return df, time.perf_counter() - t0

# session containers
if "df_api" not in st.session_state:
    st.session_state["df_api"] = None
if "df_scraped" not in st.session_state:
    st.session_state["df_scraped"] = None
if "playwright_logs" not in st.session_state:
    st.session_state["playwright_logs"] = []


# Fetch from API
if fetch_api_btn:
    with st.spinner("Fetching from ClinicalTrials.gov API..."):
        df_api, api_time = fetch_api_cached(disease, max_results_api)
        if df_api is None:
            st.error("API returned no data.")
        else:
            if "country" in df_api.columns:
                df_api["country"] = df_api["country"].apply(lambda v: canonicalize_country(v))
            st.session_state["df_api"] = df_api
            st.session_state["api_time"] = api_time
            st.success(f"API: loaded {len(df_api)} trials (t={api_time:.2f}s)")

# Run Browser Scraper (Playwright)
if run_browser_btn:
    timestamp = int(time.time())
    out_path = DATA_DIR / f"playwright_{disease.replace(' ', '_')}_{timestamp}.jsonl"
    st.info(f"Running Playwright scraper for '{disease}' (max {max_results_browser}). This runs a subprocess and may take a while. Scraping ClinicalTrials.gov is just for demonstration purposes. The API method is orders of magnitude faster for querying this website in a production environment. Records with 'unknown status' are excluded. See the README for more information.")
    with st.spinner("Running Playwright (separate process)..."):
        returncode, elapsed, logs = run_playwright_subprocess(
            script_path="analysis/playwright_scraper.py",
            disease=disease,
            max_results=int(max_results_browser),
            output_path=str(out_path),
            timeout=600
        )
    st.session_state["playwright_logs"] = logs
    if show_playwright_logs:
        with st.expander("Playwright logs (latest run)", expanded=False):
            st.text_area("", value="\n".join(logs), height=300)
    if returncode == 0 and out_path.exists():
        try:
            df_scraped = pd.read_json(out_path, lines=True)
            if "startYear" in df_scraped.columns:
                df_scraped["startYear"] = pd.to_numeric(df_scraped["startYear"], errors="coerce").astype("Int64")
            if "country" in df_scraped.columns:
                df_scraped["country"] = df_scraped["country"].apply(lambda v: canonicalize_country(v))
            st.session_state["df_scraped"] = df_scraped
            st.success(f"Playwright: loaded {len(df_scraped)} records (saved to {out_path}) in {elapsed:.1f}s")
        except Exception as e:
            st.error(f"Could not read Playwright output: {e}")
    else:
        st.error("Playwright failed. Enable 'Show Playwright debug logs' in the sidebar for details.")

# Optional: show latest logs even when not re-running (useful after errors).
if show_playwright_logs and st.session_state.get("playwright_logs"):
    with st.expander("Playwright logs (last captured)", expanded=False):
        st.text_area("", value="\n".join(st.session_state["playwright_logs"]), height=300)

# show status
df_api = st.session_state.get("df_api")
df_scraped = st.session_state.get("df_scraped")

PRIMARY_COLS = ["nctId", "briefTitle", "startYear", "country"]

# Normalize helper
def normalize_df_for_app(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame(columns=["nctId", "briefTitle", "startYear", "country"])
    df2 = df.copy()
    if "start_year" in df2.columns and "startYear" not in df2.columns:
        df2 = df2.rename(columns={"start_year": "startYear"})
    if "nct_id" in df2.columns and "nctId" not in df2.columns:
        df2 = df2.rename(columns={"nct_id": "nctId"})
    if "country" in df2.columns:
        df2["country"] = df2["country"].apply(lambda v: canonicalize_country(v))
    if "startYear" in df2.columns:
        df2["startYear"] = pd.to_numeric(df2["startYear"], errors="coerce").astype("Int64")
    return df2

df_api = normalize_df_for_app(df_api)
df_scraped = normalize_df_for_app(df_scraped)

def view_for_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    return df

st.markdown("## Data status")
# Comparison UI
c_api, c_scr = st.columns(2)
with c_api:
    st.subheader("Official API")
    if df_api is None or df_api.empty:
        st.write("No API data loaded.")
    else:
        st.write(f"Records loaded: {len(df_api)}")


with c_scr:
    st.subheader("Browser Scraper (Playwright)")
    if df_scraped is None or df_scraped.empty:
        st.write("No scraped data loaded.")
    else:
        st.write(f"Records loaded: {len(df_scraped)}")

if df_api is None and df_scraped is None:
    st.info("Click 'Fetch from Official API' or 'Run Browser Scraper (Playwright)' to load data, or upload pre-scraped JSONL/CSV.")
    st.stop()
# Raw data expanders
with st.expander("📄 Records from API data", expanded=True):
    if df_api is None or df_api.empty:
        st.write("No API data yet.")
    else:
        df_api_view = view_for_table(df_api)
        st.dataframe(df_api_view.head(500), use_container_width=True, hide_index=True)

with st.expander("📄 Records from scraped data", expanded=True):
    if df_scraped is None or df_scraped.empty:
        st.write("No scraped data yet.")
    else:
        df_scr_view = view_for_table(df_scraped)
        st.dataframe(df_scr_view.head(500), use_container_width=True, hide_index=True)

# Download buttons
dl1, dl2 = st.columns(2)
with dl1:
    if df_api is not None and not df_api.empty:
        st.download_button("⬇️ Download API CSV", df_api.to_csv(index=False), file_name=f"{disease.replace(' ','_')}_api.csv")
with dl2:
    if df_scraped is not None and not df_scraped.empty:
        st.download_button("⬇️ Download Scraped CSV", df_scraped.to_csv(index=False), file_name=f"{disease.replace(' ','_')}_playwright.csv")

# Trend comparison
st.subheader("📈 Trend comparison")
trend_api = compute_trend(df_api) if df_api is not None else None
trend_scr = compute_trend(df_scraped) if df_scraped is not None else None

fig = px.line(title=f"{disease} — API vs Browser Scraper: Trials per Year")
if trend_api is not None and not trend_api.empty:
    fig.add_scatter(x=trend_api["start_year"], y=trend_api["count"], mode="lines+markers", name="API")
if trend_scr is not None and not trend_scr.empty:
    fig.add_scatter(x=trend_scr["start_year"], y=trend_scr["count"], mode="lines+markers", name="Browser Scraper")
if fig.data:
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough year data available for trend comparison.")

# Country comparison
st.subheader("🗺️ Country comparison (top 15)")
geo_api = country_counts(df_api) if df_api is not None else None
geo_scr = country_counts(df_scraped) if df_scraped is not None else None

map_projection = st.selectbox(
    "Map projection",
    ["natural earth", "orthographic", "equirectangular"],
    index=0,
    help="Orthographic looks like a globe; natural earth is a good default.",
)

def make_country_choropleth(geo_df: pd.DataFrame, title: str):
    fig = px.choropleth(
        geo_df,
        locations="country",
        locationmode="country names",
        color="count",
        hover_name="country",
        hover_data={"count": ":,"},
        title=title,
    )
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>Trials: %{z:,}<extra></extra>",
        marker_line_color="rgba(0,0,0,0.55)",
        marker_line_width=0.8,
    )
    fig.update_geos(
        projection_type=map_projection,
        showframe=False,
        showland=True,
        landcolor="rgb(245,245,245)",
        showocean=True,
        oceancolor="rgb(225, 240, 255)",
        showlakes=True,
        lakecolor="rgb(225, 240, 255)",
        showcountries=True,
        countrycolor="rgba(0,0,0,0.55)",
        countrywidth=0.6,
        showcoastlines=True,
        coastlinecolor="rgba(0,0,0,0.75)",
        coastlinewidth=0.8,
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title="Trials"),
    )
    return fig

g1, g2 = st.columns(2)
with g1:
    st.markdown("**API — Top countries**")
    if geo_api is None or geo_api.empty:
        st.write("No country data")
    else:
        st.dataframe(geo_api.head(15), use_container_width=True, hide_index=True)
        fig_map_api = make_country_choropleth(geo_api, title="API: Trials by Country")
        st.plotly_chart(fig_map_api, use_container_width=True)
with g2:
    st.markdown("**Browser Scraper — Top countries**")
    if geo_scr is None or geo_scr.empty:
        st.write("No country data")
    else:
        st.dataframe(geo_scr.head(15), use_container_width=True, hide_index=True)
        fig_map_scr = make_country_choropleth(geo_scr, title="Browser Scraper: Trials by Country")
        st.plotly_chart(fig_map_scr, use_container_width=True)

# Heatmap
st.subheader("🔥 Heatmap of top countries (API priority)")
preferred_geo = geo_api if (geo_api is not None and not geo_api.empty) else geo_scr
if preferred_geo is None or preferred_geo.empty:
    st.info("No country data to show heatmap.")
else:
    top_geo = preferred_geo.head(15)
    fig_hm, ax = plt.subplots(figsize=(8, max(2, len(top_geo)*0.35)))
    sns.heatmap(top_geo.set_index("country").T, annot=True, fmt="d", cmap="Reds", cbar=True, ax=ax)
    ax.set_ylabel("")
    st.pyplot(fig_hm)

