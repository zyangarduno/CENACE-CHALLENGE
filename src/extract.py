"""Download MDA/MTR prices from the CENACE SW-PML web service and build the dataset."""
import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)
PRICE_COLS = ["pml", "pml_ene", "pml_per", "pml_cng"]


def build_url(api, nodes, d_start, d_end):
    """URL in the format required by the manual: nodes comma-separated, dates as Y/M/D."""
    nodos = ",".join(nodes)
    return (f"{api['base_url']}/{api['sistema']}/{api['proceso']}/{nodos}/"
            f"{d_start:%Y/%m/%d}/{d_end:%Y/%m/%d}/{api['formato']}")


def make_chunks(d_start, d_end, days):
    """Split a date range into blocks of at most `days` days (API limit: 7)."""
    chunks, current = [], d_start
    while current <= d_end:
        chunk_end = min(current + timedelta(days=days - 1), d_end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60))
def fetch(url):
    """One request, retried with exponential backoff on failure."""
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.json()


def parse_response(data):
    """Turn one API response (dict) into a typed table, one row per node and hour."""
    df = pd.json_normalize(data["Resultados"], record_path="Valores", meta="clv_nodo")
    df[PRICE_COLS] = df[PRICE_COLS].apply(pd.to_numeric)
    df["hora"] = pd.to_numeric(df["hora"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["timestamp"] = df["fecha"] + pd.to_timedelta(df["hora"] - 1, unit="h")
    return df[["clv_nodo", "timestamp", "fecha", "hora"] + PRICE_COLS]


def download_raw(cfg, raw_dir):
    """Download every missing chunk into raw_dir. Returns the list of failed chunks."""
    api, nodes = cfg["api"], cfg["nodes"]
    start = date.fromisoformat(cfg["period"]["start"])
    end = date.fromisoformat(cfg["period"]["end"])
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    chunks = make_chunks(start, end, api["max_days_per_request"])
    for d_start, d_end in chunks:
        out = raw_dir / f"{api['proceso']}_{d_start}_{d_end}.json"
        if out.exists():
            continue                     # already downloaded: lets the job resume
        try:
            data = fetch(build_url(api, nodes, d_start, d_end))
            out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            log.info("Downloaded %s to %s", d_start, d_end)
        except Exception as exc:         # recorded, not hidden
            failed.append((d_start, d_end, str(exc)))
            log.error("Failed %s to %s: %s", d_start, d_end, exc)
        time.sleep(1)                    # be polite to the server
    log.info("Chunks: %d total, %d failed", len(chunks), len(failed))
    return failed


def build_dataset(raw_dir, proceso):
    """Combine all raw files into one table."""
    files = sorted(Path(raw_dir).glob(f"{proceso}_*.json"))
    if not files:
        raise FileNotFoundError(f"No raw files for {proceso} in {raw_dir}")
    tables = [parse_response(json.loads(p.read_text(encoding="utf-8"))) for p in files]
    return pd.concat(tables, ignore_index=True)


def validate(df, n_nodes):
    """Basic data checks. Raises an error if the dataset is not as expected."""
    assert df["clv_nodo"].nunique() == n_nodes, "unexpected number of nodes"
    assert not df.duplicated(["clv_nodo", "timestamp"]).any(), "duplicate node-hours"
    hours = df.groupby("clv_nodo")["timestamp"].count()
    assert hours.nunique() == 1, "nodes have different numbers of hours"
    gap = (df["pml_ene"] + df["pml_per"] + df["pml_cng"] - df["pml"]).abs().max()
    assert gap < 0.05, f"components do not add up to the price (max gap {gap:.2f})"
    log.info("Data checks passed: %d rows, %d hours per node", len(df), hours.iloc[0])
