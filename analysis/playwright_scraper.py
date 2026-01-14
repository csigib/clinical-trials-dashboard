#!/usr/bin/env python
"""analysis/playwright_scraper.py

Compact Playwright browser scraper used by app.py via analysis/playwright_runner.py.

Writes JSONL with keys expected by app.py:
  - nctId
  - briefTitle
  - startYear
  - country
"""

from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright


DEFAULT_TIMEOUT_MS = 30000


def _has_chrome_headless_shell(playwright_cache_dir: Path) -> bool:
    try:
        for bundle_dir in playwright_cache_dir.glob("chromium_headless_shell-*"):
            exe = bundle_dir / "chrome-headless-shell-linux64" / "chrome-headless-shell"
            if exe.exists():
                return True
    except Exception:
        return False
    return False


def _ensure_playwright_browsers_installed(timeout_seconds: int = 600) -> None:
    # Streamlit Community Cloud can sometimes end up with Playwright installed but browsers missing.
    # This makes the scraper resilient even if postBuild didn't persist or got skipped.
    if not sys.platform.startswith("linux"):
        return

    cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not cache:
        return

    cache_dir = Path(cache)
    if _has_chrome_headless_shell(cache_dir):
        return

    print(f"INFO_PLAYWRIGHT_INSTALL: missing browsers in {cache_dir}; downloading Playwright browsers once")
    cache_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(cache_dir)

    # Playwright downloads are performed by a bundled Node.js tool; suppress noisy deprecation warnings.
    node_opts = env.get("NODE_OPTIONS", "")
    if "--no-deprecation" not in node_opts:
        env["NODE_OPTIONS"] = (node_opts + " --no-deprecation").strip()

    cmd = [sys.executable, "-m", "playwright", "install", "chromium", "chromium-headless-shell"]
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_seconds,
        )

        verbose = os.environ.get("PLAYWRIGHT_INSTALL_VERBOSE", "").strip().lower() in {"1", "true", "yes"}
        if proc.returncode != 0:
            print(f"WARN_PLAYWRIGHT_INSTALL_FAILED rc={proc.returncode}")
            if proc.stdout:
                print(proc.stdout)
        else:
            if verbose and proc.stdout:
                print(proc.stdout)
    except Exception as exc:
        print(f"WARN_PLAYWRIGHT_INSTALL_EXCEPTION {type(exc).__name__}: {exc}")

    # Re-check after attempting install.
    if not _has_chrome_headless_shell(cache_dir):
        print(
            "WARN_PLAYWRIGHT_BROWSERS_STILL_MISSING: headless shell executable not found; "
            "Playwright launch may still fail."
        )


def _clean_text(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    s = str(val)
    s = s.replace("\u00A0", " ").replace("\ufeff", "")
    s = re.sub(r"[\u200B-\u200F]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _canonical_nct(val: Optional[str]) -> Optional[str]:
    s = _clean_text(val)
    if not s:
        return None
    m = re.search(r"\bNCT\s*(\d{4,})\b", s, flags=re.IGNORECASE)
    return f"NCT{m.group(1)}" if m else s


def _extract_year(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    t = str(text)
    m = re.search(r"\b(19|20)\d{2}\b", t)
    if m:
        return int(m.group(0))
    m2 = re.search(r"(\d{4})", t)
    return int(m2.group(1)) if m2 else None


def _pairs_from_search_page(page) -> List[Dict[str, Optional[str]]]:
    try:
        page.wait_for_selector(".nct-id", timeout=5000)
    except Exception:
        return []

    js = (
        "els => els.map(el => {"
        "  let container = el.closest('div');"
        "  while (container) {"
        "    const link = container.querySelector('a[href^=\"/study/\"], a[href*=\"/study/\"]') || container.querySelector('header a, h1 a, h2 a, h3 a, a');"
        "    const titleText = link ? (link.innerText || link.textContent || '') : '';"
        "    const locSpan = container.querySelector('.cities-grid .location-text span');"
        "    let country = null;"
        "    if (locSpan) {"
        "      const locText = (locSpan.innerText || '').trim();"
        "      const parts = locText.split(',');"
        "      country = parts.length ? parts[parts.length - 1].trim() : locText;"
        "    }"
        "    if (link || locSpan) {"
        "      return { nct: (el.innerText || '').trim(), url: link ? link.href : null, country, briefTitle: titleText };"
        "    }"
        "    container = container.parentElement;"
        "  }"
        "  return { nct: (el.innerText || '').trim(), url: null, country: null, briefTitle: null };"
        "})"
    )

    try:
        raw = page.eval_on_selector_all(".nct-id", js)
    except Exception:
        raw = []

    out: List[Dict[str, Optional[str]]] = []
    for r in raw or []:
        out.append(
            {
                "nctId": _canonical_nct(r.get("nct")),
                "url": r.get("url"),
                "briefTitle": _clean_text(r.get("briefTitle")),
                "country": _clean_text(r.get("country")),
            }
        )
    return out


def _extract_title_and_start_year(detail_page, timeout_ms: int) -> tuple[Optional[str], Optional[int]]:
    brief_title: Optional[str] = None
    start_year: Optional[int] = None

    def _norm_js(selector: str) -> Optional[str]:
        try:
            val = detail_page.eval_on_selector(
                selector,
                """el => {
                    if (!el) return null;
                    const t = (el.textContent || el.innerText || '');
                    return t.replace(/\\s+/g, ' ').trim();
                }""",
            )
            return _clean_text(val)
        except Exception:
            return None

    def _meta_content(selector: str) -> Optional[str]:
        try:
            val = detail_page.eval_on_selector(selector, "el => el ? (el.getAttribute('content') || '') : null")
            val = _clean_text(val)
            return val or None
        except Exception:
            return None

    # Primary selector (works for most studies; also handles nested <mark> tags).
    try:
        detail_page.wait_for_selector("h2.brief-title", timeout=min(8000, timeout_ms))
    except Exception:
        pass
    brief_title = _norm_js("h2.brief-title")

    # Fallbacks (some pages render the title elsewhere).
    if not brief_title:
        brief_title = _meta_content('meta[property="og:title"]') or _meta_content('meta[name="twitter:title"]')

    if brief_title:
        # og:title / document.title often includes a suffix like " - ClinicalTrials.gov"
        brief_title = re.sub(r"\s+-\s+ClinicalTrials\.gov\s*$", "", brief_title, flags=re.IGNORECASE).strip()

    if not brief_title:
        try:
            page_title = _clean_text(detail_page.title())
            if page_title:
                page_title = re.sub(r"\s+-\s+ClinicalTrials\.gov\s*$", "", page_title, flags=re.IGNORECASE).strip()
                page_title = re.sub(r"\s+-\s+Full Text View\s*$", "", page_title, flags=re.IGNORECASE).strip()
            brief_title = page_title or None
        except Exception:
            brief_title = None

    if not brief_title:
        # As a last resort, grab the first h1 (but avoid the site header itself).
        t = _norm_js("main h1") or _norm_js("h1")
        if t and "clinicaltrials" not in t.lower():
            brief_title = t

    sel = "div.overview-col-wide span.study-overview-item-text"
    try:
        detail_page.wait_for_selector(sel, timeout=timeout_ms)
        el = detail_page.query_selector(sel)
        if el:
            start_year = _extract_year(_clean_text(el.inner_text()))
    except Exception:
        start_year = None

    return brief_title, start_year


def scrape(disease: str, max_results: int, output_path: Path, headless: bool = True, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> int:
    search_url = f"https://clinicaltrials.gov/search?cond={disease}"
    pairs: List[Dict[str, Optional[str]]] = []
    seen: set[str] = set()
    records: List[Dict[str, Any]] = []

    # On Streamlit Community Cloud, build/run may happen under different users.
    # Use a project-local Playwright browser cache so Chromium is found reliably.
    if sys.platform.startswith("linux"):
        os.environ.setdefault(
            "PLAYWRIGHT_BROWSERS_PATH",
            str((Path(__file__).resolve().parents[1] / ".playwright-browsers")),
        )

        # Best-effort: ensure browsers exist before starting Playwright.
        _ensure_playwright_browsers_installed()

    with sync_playwright() as p:
        launch_args: List[str] = []
        # Streamlit Community Cloud runs in a restricted Linux container where Chromium sandboxing
        # and /dev/shm sizing can cause launch crashes.
        if sys.platform.startswith("linux"):
            launch_args.extend(["--no-sandbox", "--disable-dev-shm-usage"])

        browser = p.chromium.launch(headless=headless, args=launch_args)
        page = browser.new_page()
        page.goto(search_url, timeout=timeout_ms)

        while len(pairs) < max_results:
            for it in _pairs_from_search_page(page):
                nct = it.get("nctId")
                if not nct or nct in seen:
                    continue
                pairs.append(it)
                seen.add(nct)
                if len(pairs) >= max_results:
                    break

            if len(pairs) >= max_results:
                break

            next_btn = page.query_selector('[aria-label="Next page"]')
            if not next_btn:
                break
            try:
                aria_disabled = next_btn.get_attribute("aria-disabled")
                if aria_disabled and aria_disabled.lower() == "true":
                    break
            except Exception:
                pass
            try:
                next_btn.click(timeout=timeout_ms)
            except Exception:
                break

        for it in pairs[:max_results]:
            nct_id = it.get("nctId")
            url = it.get("url")
            if not nct_id or not url:
                continue

            detail = None
            brief_title = None
            start_year = None
            try:
                detail = browser.new_page()
                detail.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                brief_title, start_year = _extract_title_and_start_year(detail, timeout_ms)
            finally:
                try:
                    if detail:
                        detail.close()
                except Exception:
                    pass

            if brief_title and "unknown status" in brief_title.lower():
                continue

            final_title = brief_title or it.get("briefTitle")
            if not final_title:
                print(f"WARN_TITLE_NONE nctId={nct_id} url={url}")

            records.append(
                {
                    "nctId": nct_id,
                    "briefTitle": final_title,
                    "startYear": start_year,
                    "country": it.get("country"),
                }
            )

        browser.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for rec in records[:max_results]:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return len(records[:max_results])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--disease", required=True)
    parser.add_argument("--max_results", type=int, default=25)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    args = parser.parse_args()

    try:
        n = scrape(
            disease=args.disease,
            max_results=int(args.max_results),
            output_path=Path(args.output),
            headless=bool(args.headless),
            timeout_ms=int(args.timeout),
        )
        print(f"SCRAPED_ITEMS={n}")
    except Exception as exc:
        # Make sure the subprocess logs contain the real cause on Streamlit Cloud.
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
