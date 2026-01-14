import pandas as pd
from typing import Optional
import pycountry

_MANUAL_COUNTRY_MAP = {
    "USA": "United States",
    "U.S.": "United States",
    "U.S.A.": "United States",
    "US": "United States",
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "England": "United Kingdom",
    "Korea, Republic of": "South Korea",
    "People's Republic of China": "China",
    "PRC": "China",
    "Great Britain": "United Kingdom"
}

def canonicalize_country(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    n = str(name).strip()
    if not n:
        return None
    if n in _MANUAL_COUNTRY_MAP:
        return _MANUAL_COUNTRY_MAP[n]
    try:
        c = pycountry.countries.lookup(n)
        return c.name
    except Exception:
        try:
            results = pycountry.countries.search_fuzzy(n)
            if results:
                return results[0].name
        except Exception:
            pass
    return n.title()

def country_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["country", "count"])
    if "country" not in df.columns:
        return pd.DataFrame(columns=["country", "count"])
    tmp = df.copy()
    tmp["country"] = tmp["country"].apply(canonicalize_country)
    tmp = tmp[tmp["country"].notna()]
    if tmp.empty:
        return pd.DataFrame(columns=["country", "count"])
    counts = tmp.groupby("country").size().reset_index(name="count").sort_values("count", ascending=False)
    return counts