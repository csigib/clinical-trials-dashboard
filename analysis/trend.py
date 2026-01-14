import pandas as pd

def compute_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return DataFrame with columns ['start_year','count'] derived from df['startYear'].
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["start_year", "count"])
    if "startYear" not in df.columns:
        return pd.DataFrame(columns=["start_year", "count"])
    tmp = df.dropna(subset=["startYear"]).copy()
    if tmp.empty:
        return pd.DataFrame(columns=["start_year", "count"])
    grouped = tmp.groupby("startYear").size().reset_index(name="count").sort_values("startYear")
    grouped = grouped.rename(columns={"startYear": "start_year"})
    return grouped