#!/usr/bin/env python3
"""Sync publication data for the portfolio."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.json"
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
USER_AGENT = "Mozilla/5.0 (compatible; PortfolioSync/1.0; +https://abdrrahim.com)"


def fetch_text(url: str, accept: Optional[str] = None) -> str:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept

    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_json(url: str, accept: Optional[str] = "application/json") -> dict:
    return json.loads(fetch_text(url, accept=accept))


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def parse_orcid_works(orcid: str) -> List[dict]:
    data = fetch_json(f"https://pub.orcid.org/v3.0/{orcid}/works")
    works = []

    for group in data.get("group", []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue

        summary = summaries[0]
        title = (((summary.get("title") or {}).get("title") or {}).get("value") or "").strip()
        if not title:
            continue

        publication_date = summary.get("publication-date") or {}
        year = (publication_date.get("year") or {}).get("value")
        month = (publication_date.get("month") or {}).get("value") or "01"
        day = (publication_date.get("day") or {}).get("value") or "01"
        published = f"{year}-{month.zfill(2)}-{day.zfill(2)}" if year else None

        links = []
        for external_id in summary.get("external-ids", {}).get("external-id", []):
            if external_id.get("external-id-type") == "doi":
                doi_value = external_id.get("external-id-value")
                if doi_value:
                    links.append({"label": "DOI", "href": f"https://doi.org/{doi_value}"})

        works.append(
            {
                "title": title,
                "published": published,
                "venue": summary.get("journal-title", {}).get("value") or "ORCID",
                "authors": "",
                "links": links,
                "source": "ORCID"
            }
        )

    return works


def parse_nist_publications(nist_url: str) -> List[dict]:
    html = fetch_text(nist_url)
    items = []
    pattern = re.compile(
        r'<h3[^>]*>\s*<a[^>]+href="(?P<href>[^"]+)".*?<span>(?P<title>.*?)</span>.*?</a>\s*</h3>.*?'
        r'<time[^>]+datetime="(?P<datetime>\d{4}-\d{2}-\d{2})[^"]*">.*?</time>.*?'
        r'<div class="nist-field__item">(?P<authors>.*?)</div>',
        re.S
    )

    month_lookup = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"
    }

    for match in pattern.finditer(html):
        title = re.sub(r"\s+", " ", match.group("title")).strip()
        authors = re.sub(r"<[^>]+>", "", match.group("authors"))
        authors = re.sub(r"\s+", " ", authors).replace(" ,", ",").strip()
        href = match.group("href").strip()
        published = match.group("datetime").strip()

        items.append(
            {
                "title": title,
                "published": published,
                "venue": "NIST",
                "authors": authors,
                "links": [{"label": "NIST", "href": href if href.startswith("http") else f"https://www.nist.gov{href}"}],
                "source": "NIST"
            }
        )

    return items


def parse_google_scholar(scholar_url: str) -> List[dict]:
    html = fetch_text(scholar_url)
    rows = re.findall(r'<tr class="gsc_a_tr">.*?</tr>', html, re.S)

    items = []
    for row in rows:
        title_match = re.search(r'<a[^>]*href="(?P<href>[^"]+)"[^>]*class="gsc_a_at"[^>]*>(?P<title>.*?)</a>', row, re.S)
        authors_match = re.search(r'<div class="gs_gray">(?P<authors>.*?)</div>', row, re.S)
        venue_matches = re.findall(r'<div class="gs_gray">(?P<venue>.*?)</div>', row, re.S)
        citation_match = re.search(r'class="gsc_a_ac gs_ibl">(?P<cited>\d+)</a>', row, re.S)
        year_match = re.search(r'<td class="gsc_a_y">.*?<span[^>]*>(?P<year>\d{4})</span>', row, re.S)

        if not title_match or not year_match:
            continue

        href = title_match.group("href")
        title = title_match.group("title")
        authors = authors_match.group("authors") if authors_match else ""
        venue = venue_matches[1] if len(venue_matches) > 1 else ""
        cited = citation_match.group("cited") if citation_match else "0"
        year = year_match.group("year")

        items.append(
            {
                "title": re.sub(r"\s+", " ", title).strip(),
                "published": f"{year}-01-01",
                "venue": re.sub(r"\s+", " ", venue).strip() or "Google Scholar",
                "authors": re.sub(r"\s+", " ", authors).strip(),
                "links": [{"label": "Scholar", "href": f"https://scholar.google.com{href}"}],
                "source": "Google Scholar",
                "citationCount": int(cited or 0)
            }
        )

    return items


def dedupe_items(items: Iterable[dict]) -> List[dict]:
    merged: Dict[str, dict] = {}

    for item in items:
        key = normalize_title(item["title"])
        current = merged.get(key)
        if not current:
            merged[key] = item
            continue

        existing_links = {(link["label"], link["href"]) for link in current.get("links", [])}
        for link in item.get("links", []):
            pair = (link["label"], link["href"])
            if pair not in existing_links:
                current.setdefault("links", []).append(link)

        if not current.get("authors") and item.get("authors"):
            current["authors"] = item["authors"]

        if current.get("venue") in ("ORCID", "Google Scholar") and item.get("venue"):
            current["venue"] = item["venue"]

        current["citationCount"] = max(current.get("citationCount", 0), item.get("citationCount", 0))

        current_date = current.get("published") or ""
        new_date = item.get("published") or ""
        if new_date and (not current_date or new_date > current_date):
            current["published"] = new_date

    return sorted(merged.values(), key=lambda item: item.get("published") or "", reverse=True)


def load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orcid", help="Override the ORCID id")
    parser.add_argument("--nist-url", help="Override the NIST profile URL")
    parser.add_argument("--scholar-url", help="Optional public Google Scholar citations URL")
    args = parser.parse_args()

    profile = load_profile()
    orcid = args.orcid or profile["links"]["orcid"]["href"].rstrip("/").split("/")[-1]
    nist_url = args.nist_url or profile["links"]["nist"]["href"]
    scholar_url = args.scholar_url or profile["links"]["scholar"]["href"]
    if scholar_url.rstrip("/") == "https://scholar.google.com":
        scholar_url = None

    collected: List[dict] = []
    sources: List[str] = []

    for label, action in (
        ("ORCID", lambda: parse_orcid_works(orcid)),
        ("NIST", lambda: parse_nist_publications(nist_url))
    ):
        try:
            items = action()
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            print(f"{label} sync failed: {error}", file=sys.stderr)
            continue
        collected.extend(items)
        sources.append(label)

    if scholar_url:
        try:
            collected.extend(parse_google_scholar(scholar_url))
            sources.append("Google Scholar")
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"Google Scholar sync failed: {error}", file=sys.stderr)

    payload = {
        "updatedAt": str(date.today()),
        "sources": sources,
        "publications": dedupe_items(collected)
    }
    PUBLICATIONS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload['publications'])} publications to {PUBLICATIONS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
