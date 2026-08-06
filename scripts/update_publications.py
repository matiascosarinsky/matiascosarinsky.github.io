#!/usr/bin/env python3
"""Refresh publications from Matias's Google Scholar profile.

Optional project/code/demo/dataset links live in data/publication-overrides.json
because bibliographic services generally cannot infer those links safely.
"""

import json
from io import BytesIO
import re
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader
try:
    import pymupdf as fitz
except ImportError:
    fitz = None
from scholarly import scholarly

ROOT = Path(__file__).resolve().parents[1]
SCHOLAR_ID = "j7pWCTgAAAAJ"
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
OVERRIDES_PATH = ROOT / "data" / "publication-overrides.json"
LINKS_PATH = ROOT / "assets" / "publication-links.json"
FIGURES_DIR = ROOT / "assets" / "figures"
EXCLUDED_TITLE_FRAGMENTS = ("juliageodynamics/geoparams",)


def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def title_key(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())


def figure_slug(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return "-".join(words[:10]) or "publication"


def figure_path(title):
    folder = FIGURES_DIR / figure_slug(title)
    folder.mkdir(parents=True, exist_ok=True)
    supported = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"}
    files = sorted(file for file in folder.iterdir() if file.is_file() and file.suffix.lower() in supported)
    image_files = [file for file in files if file.suffix.lower() != ".pdf"]
    if image_files:
        return f"assets/figures/{folder.name}/{image_files[0].name}"
    if files and files[0].suffix.lower() == ".pdf":
        thumbnail = folder / "figure-1.png"
        if not thumbnail.exists() and fitz is not None:
            document = fitz.open(files[0])
            page = document.load_page(0)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pixmap.save(thumbnail)
            document.close()
        if thumbnail.exists():
            return f"assets/figures/{folder.name}/{thumbnail.name}"
        print("PyMuPDF is not installed; skipping PDF thumbnail generation.", file=sys.stderr)
        return ""
    if not files:
        return ""


def authors_from(value):
    if isinstance(value, list):
        return [clean(name) for name in value if clean(name)]
    return [clean(name) for name in re.split(r",\s*|\s+and\s+", value or "") if clean(name)]


def read_json_object(path):
    if not path.exists():
        return {}
    contents = path.read_text().strip()
    return json.loads(contents) if contents else {}


def infer_equal_contributors(paper_url, authors):
    """Best-effort detection of asterisked equal contributors in an arXiv PDF."""
    if "arxiv.org/abs/" not in paper_url and "arxiv.org/pdf/" not in paper_url:
        return []
    pdf_url = re.sub(r"/abs/", "/pdf/", paper_url).split("?")[0]
    if not pdf_url.endswith(".pdf"):
        pdf_url += ".pdf"
    try:
        request = urllib.request.Request(pdf_url, headers={"User-Agent": "matiascosarinsky.github.io publication updater"})
        with urllib.request.urlopen(request, timeout=30) as response:
            reader = PdfReader(BytesIO(response.read()))
        first_pages = "\n".join((page.extract_text() or "") for page in reader.pages[:2])
        equal_language = re.search(r"equal contribution|contributed equally|co[- ]first authors?", first_pages, re.I)
        if not equal_language:
            return []
        found = []
        for author in authors:
            pattern = rf"{re.escape(author)}\s*[*†‡]"
            if re.search(pattern, first_pages, re.I):
                found.append(author)
        return found
    except Exception as error:
        print(f"Could not inspect PDF for equal contribution: {error}", file=sys.stderr)
        return []


def main():
    try:
        author = scholarly.search_author_id(SCHOLAR_ID)
        author = scholarly.fill(author, sections=["basics", "publications"])
    except Exception as error:
        print(f"Could not fetch Google Scholar data: {error}", file=sys.stderr)
        return 1

    overrides = read_json_object(OVERRIDES_PATH)
    manual_links = read_json_object(LINKS_PATH)
    override_map = {title_key(title): value for title, value in overrides.items()}
    manual_link_map = {title_key(title): value for title, value in manual_links.items()}
    publications = []
    new_titles = []

    for entry in author.get("publications", []):
        try:
            entry = scholarly.fill(entry)
        except Exception as error:
            print(f"Could not enrich publication; using Scholar summary: {error}", file=sys.stderr)
        bib = entry.get("bib", {})
        title = clean(bib.get("title"))
        normalized_title = re.sub(r"\s+", "", title.lower())
        if any(fragment.replace(" ", "") in normalized_title for fragment in EXCLUDED_TITLE_FRAGMENTS):
            continue
        authors = authors_from(bib.get("author"))
        year = clean(bib.get("pub_year"))
        publication_key = title_key(title)
        has_manual_entry = publication_key in manual_link_map
        if not has_manual_entry:
            new_titles.append(title)
        manual = manual_link_map.get(publication_key, {})
        paper = clean(
            manual.get("paper")
            if has_manual_entry
            else (
                entry.get("pub_url")
                or bib.get("url")
                or entry.get("eprint")
                or bib.get("eprint")
            )
        )
        override = override_map.get(title_key(title), {})
        links = []
        link_fields = (
            ("project_page", "Project Page"),
            ("paper", "Paper"),
            ("code", "Code"),
            ("dataset", "Dataset"),
            ("demo", "Demo"),
        )
        for field, label in link_fields:
            url = paper if field == "paper" else clean(manual.get(field))
            if url:
                links.append({"label": label, "url": url})
        equal_contributors = override.get("equal_contributors", []) or infer_equal_contributors(paper, authors)
        publications.append({
            "title": title,
            "authors": authors,
            "year": int(year) if year.isdigit() else year,
            "venue": clean(bib.get("venue") or bib.get("journal") or bib.get("conference")),
            "links": links,
            "figure": figure_path(title),
            "equal_contributors": equal_contributors,
        })

    publications.sort(key=lambda item: (str(item["year"]), item["title"]), reverse=True)
    updated_links = dict(manual_links)
    for publication in publications:
        key = title_key(publication["title"])
        if key in manual_link_map:
            continue
        existing = {}
        scholar_paper = next(
            (link["url"] for link in publication["links"] if link["label"] == "Paper"),
            "",
        )
        updated_links[publication["title"]] = {
            "project_page": "",
            "paper": scholar_paper,
            "code": "",
            "dataset": "",
            "demo": "",
        }
    LINKS_PATH.write_text(json.dumps(updated_links, indent=2, ensure_ascii=False) + "\n")
    PUBLICATIONS_PATH.write_text(json.dumps(publications, indent=2, ensure_ascii=False) + "\n")
    print(f"Updated {len(publications)} publications from Google Scholar.")
    for title in new_titles:
        print(f"NEW_PUBLICATION: {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
