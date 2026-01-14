import re
import requests
import pandas as pd
from typing import Optional

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

def _extract_year(value: Optional[str]) -> Optional[int]:
    """Return first 4-digit year found in value (or None)."""
    if value is None:
        return None
    # If lists are passed accidentally, use first element
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    s = str(value)
    m = re.search(r"(\d{4})", s)
    return int(m.group(1)) if m else None

def get_clinical_trials(disease: str, page_size: int = 100, params_override: dict = None) -> pd.DataFrame:
    """
    Query ClinicalTrials.gov v2 API for `disease`. Returns a pandas DataFrame with columns:
    ['nctId', 'briefTitle', 'startYear', 'country'].
    """
    params = {
        "query.cond": disease,
        "pageSize": page_size
    }
    if params_override:
        params.update(params_override)

    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    records = []
    for s in payload.get("studies", []):
        ident = s.get("protocolSection", {}).get("identificationModule", {})
        design = s.get("protocolSection", {}).get("designModule", {})

        nct_id = ident.get("nctId") or ident.get("id")
        brief_title = ident.get("briefTitle") or ident.get("officialTitle")

        # country: first location (if present)
        locs = s.get("protocolSection", {}).get("contactsLocationsModule", {}).get("locations") or []
        country = None
        if locs and isinstance(locs, (list, tuple)) and isinstance(locs[0], dict):
            country = locs[0].get("country")

        # start date -> year (defensive)
        start_date = s.get("protocolSection", {}).get("statusModule", {}).get("startDateStruct", {}).get("date")
        start_year = _extract_year(start_date)

        records.append({
            "nctId": nct_id,
            "briefTitle": brief_title,
            "startYear": start_year,
            "country": country,
        })

    df = pd.DataFrame(records, columns=["nctId", "briefTitle", "startYear", "country"])
    # ensure startYear is nullable integer dtype
    df["startYear"] = pd.to_numeric(df["startYear"], errors="coerce").astype("Int64")
    return df