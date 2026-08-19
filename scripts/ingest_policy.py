#!/usr/bin/env python3
"""Build the curated local ACECQA policy corpus.

Preferred (reproducible) path:
    1. Download ACECQA's official Guide to the NQF PDF in a normal browser.
    2. Run:
       python scripts/ingest_policy.py --pdf ~/Downloads/<guide-file>.pdf

HTML ingestion remains available for environments where ACECQA permits scripted
requests, but ACECQA may return HTTP 403 to non-browser clients. The PDF path is
therefore the recommended Milestone 3 ingestion mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit(
        "Policy ingestion dependencies are missing. Run: pip install -e '.[policy]'"
    ) from exc

try:
    from pypdf import PdfReader
except ImportError as exc:
    raise SystemExit(
        "PDF ingestion dependency is missing. Run: pip install -e '.[policy]'"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "policy" / "sources.json"
DEFAULT_OUTPUT = ROOT / "data" / "policy" / "policy_chunks.jsonl"
DEFAULT_SNAPSHOT = ROOT / "data" / "policy" / "corpus_manifest.json"
SPACE_RE = re.compile(r"\s+")

# Official ACECQA downloadable Guide to the NQF resource. The browser-facing
# Guide page currently links to this media resource. Keep the URL as provenance;
# the PDF bytes are read from a local user-downloaded file so ingestion does not
# depend on bypassing ACECQA's anti-bot controls.
GUIDE_PDF_SOURCE = {
    "source_id": "guide_nqf_pdf",
    "title": "Guide to the National Quality Framework",
    "url": "https://www.acecqa.gov.au/media/38281",
    "source_kind": "official_pdf",
    "authority_level": "official_guidance",
}

ALL_GUIDE_TOPICS = {
    "nqf_overview",
    "legal_hierarchy",
    "guide_updates",
    "nqs",
    "quality_ratings",
    "assessment_rating",
    "working_towards_nqs",
    "quality_improvement",
    "qip",
    "significant_improvement_required",
    "regulatory_powers",
    "monitoring",
    "enforcement",
    "proportionality",
    "risk",
    "compliance_tools",
    "good_regulatory_practice",
    "enforceable_undertakings",
    "acecqa_role",
    "operational_requirements",
}


def clean_text(value: str) -> str:
    return SPACE_RE.sub(" ", value).strip()


def fetch_html(url: str, *, timeout: int = 30, retries: int = 3) -> str:
    """Fetch an ACECQA HTML page when scripted access is allowed.

    A 403 is treated as a site-access constraint, not something to bypass. The
    caller is instructed to use the official downloadable PDF instead.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 403:
                raise RuntimeError(
                    "ACECQA returned HTTP 403 to scripted HTML access. "
                    "Do not keep retrying or add browser automation. Download the official "
                    "Guide to the NQF PDF in Safari/Chrome and run: "
                    "python scripts/ingest_policy.py --pdf /path/to/guide.pdf"
                )
            response.raise_for_status()
            return response.text
        except RuntimeError:
            raise
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def select_content_root(soup: BeautifulSoup):
    for selector in ["main", "article", ".node__content", "#block-acecqa-content", "body"]:
        node = soup.select_one(selector)
        if node is not None:
            return node
    return soup


def extract_sections(html: str) -> list[tuple[str, list[str]]]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "form"]):
        tag.decompose()

    root = select_content_root(soup)
    sections: list[tuple[str, list[str]]] = []
    current_heading = "Overview"
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_parts
        cleaned = []
        seen = set()
        for part in current_parts:
            text = clean_text(part)
            if len(text) < 25 or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        if cleaned:
            sections.append((current_heading, cleaned))
        current_parts = []

    for element in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
        name = element.name.lower()
        text = clean_text(element.get_text(" ", strip=True))
        if not text:
            continue
        if name in {"h1", "h2", "h3", "h4"}:
            flush()
            current_heading = text[:300]
        else:
            current_parts.append(text)
    flush()
    return sections


def chunk_section(parts: list[str], *, max_chars: int = 1800, overlap_parts: int = 1) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for part in parts:
        addition = len(part) + (1 if current else 0)
        if current and current_len + addition > max_chars:
            chunks.append("\n".join(current))
            current = current[-overlap_parts:] if overlap_parts else []
            current_len = sum(len(x) + 1 for x in current)
        current.append(part)
        current_len += addition
    if current:
        chunks.append("\n".join(current))
    return chunks


def build_source_chunks(source: dict, html: str, retrieved_at: str) -> list[dict]:
    chunks: list[dict] = []
    sequence = 1
    for section, parts in extract_sections(html):
        for text in chunk_section(parts):
            if len(text) < 80:
                continue
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            chunks.append(
                {
                    "chunk_id": f"POL-{source['source_id']}-{sequence:04d}",
                    "source_id": source["source_id"],
                    "source_title": source["title"],
                    "source_url": source["url"],
                    "source_kind": source["source_kind"],
                    "authority_level": source["authority_level"],
                    "topics": source.get("topics", []),
                    "keywords": source.get("keywords", []),
                    "section": section,
                    "text": text,
                    "content_sha256": digest,
                    "source_retrieved_at": retrieved_at,
                }
            )
            sequence += 1
    return chunks


def _detect_guide_section(text: str, previous: str) -> str:
    upper = text.upper()
    # These headings appear at chapter boundaries in the official Guide PDF.
    if "SECTION 1" in upper and "INTRODUCTION" in upper:
        return "Section 1: Introduction"
    if "SECTION 2" in upper and "APPLICATIONS" in upper and "APPROVALS" in upper:
        return "Section 2: Applications and Approvals"
    if "SECTION 3" in upper and "NATIONAL QUALITY" in upper and "ASSESSMENT" in upper:
        return "Section 3: National Quality Standard and Assessment and Rating"
    if "SECTION 4" in upper and "OPERATIONAL" in upper and "REQUIREMENTS" in upper:
        return "Section 4: Operational Requirements"
    if "SECTION 5" in upper and "REGULATORY AUTHORITY" in upper and "POWERS" in upper:
        return "Section 5: Regulatory Authority Powers"
    if "SECTION 6" in upper and "REVIEWS" in upper:
        return "Section 6: Reviews"
    if "SECTION 7" in upper and "GLOSSARY" in upper:
        return "Section 7: Glossary"
    return previous


def _topics_for_pdf_chunk(section: str, text: str) -> list[str]:
    topics: set[str] = set()
    lower = text.lower()

    if section.startswith("Section 1"):
        topics.update({"nqf_overview", "legal_hierarchy", "guide_updates", "acecqa_role"})
    elif section.startswith("Section 3"):
        topics.update({"nqs", "quality_ratings", "assessment_rating", "quality_improvement", "qip"})
    elif section.startswith("Section 4"):
        topics.add("operational_requirements")
    elif section.startswith("Section 5"):
        topics.update({"regulatory_powers", "monitoring", "enforcement", "risk", "good_regulatory_practice"})

    if "working towards" in lower:
        topics.update({"working_towards_nqs", "quality_ratings", "assessment_rating"})
    if "significant improvement required" in lower:
        topics.update({"significant_improvement_required", "quality_ratings", "assessment_rating"})
    if "compliance tool" in lower or "compliance notice" in lower or "compliance direction" in lower:
        topics.update({"compliance_tools", "enforcement"})
    if "enforceable undertaking" in lower:
        topics.update({"enforceable_undertakings", "compliance_tools", "enforcement"})
    if "proportionate" in lower or "proportionality" in lower:
        topics.update({"proportionality", "good_regulatory_practice"})
    if "risk to children" in lower or "assessing risk" in lower:
        topics.add("risk")
    if "regulatory authority" in lower and "acecqa" in lower:
        topics.add("acecqa_role")
    if "national law" in lower and "national regulations" in lower:
        topics.add("legal_hierarchy")

    # Topic filtering should never make a useful official Guide chunk unreachable.
    # If no narrower topic was inferred, expose it to the broad overview topic.
    if not topics:
        topics.add("nqf_overview")
    return sorted(topics & ALL_GUIDE_TOPICS)


def _keywords_for_pdf_chunk(text: str) -> list[str]:
    lower = text.lower()
    candidates = [
        "Working Towards NQS",
        "Meeting NQS",
        "Significant Improvement Required",
        "regulatory authority",
        "ACECQA",
        "National Law",
        "National Regulations",
        "compliance history",
        "risk to children",
        "proportionate",
        "compliance notice",
        "compliance direction",
        "enforceable undertaking",
        "assessment and rating",
        "Quality Improvement Plan",
    ]
    return [item for item in candidates if item.lower() in lower]


def _split_pdf_page(text: str, *, max_chars: int = 1800, overlap_chars: int = 250) -> list[str]:
    text = clean_text(text)
    if len(text) <= max_chars:
        return [text] if len(text) >= 80 else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # Prefer a sentence boundary near the end of the window.
            boundary = max(text.rfind(". ", start + int(max_chars * 0.65), end),
                           text.rfind("; ", start + int(max_chars * 0.65), end))
            if boundary > start:
                end = boundary + 1
        piece = text[start:end].strip()
        if len(piece) >= 80:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return chunks


def build_pdf_chunks(pdf_path: Path, retrieved_at: str) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    if not reader.pages:
        raise RuntimeError(f"PDF has no pages: {pdf_path}")

    chunks: list[dict] = []
    sequence = 1
    current_section = "Guide to the NQF"

    for page_index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        page_text = clean_text(raw_text)
        if len(page_text) < 80:
            continue

        current_section = _detect_guide_section(page_text[:2500], current_section)
        for text in _split_pdf_page(page_text):
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            topics = _topics_for_pdf_chunk(current_section, text)
            chunks.append(
                {
                    "chunk_id": f"POL-{GUIDE_PDF_SOURCE['source_id']}-{sequence:04d}",
                    "source_id": GUIDE_PDF_SOURCE["source_id"],
                    "source_title": GUIDE_PDF_SOURCE["title"],
                    "source_url": GUIDE_PDF_SOURCE["url"],
                    "source_kind": GUIDE_PDF_SOURCE["source_kind"],
                    "authority_level": GUIDE_PDF_SOURCE["authority_level"],
                    "topics": topics,
                    "keywords": _keywords_for_pdf_chunk(text),
                    "section": f"{current_section} - PDF page {page_index}",
                    "page_number": page_index,
                    "text": text,
                    "content_sha256": digest,
                    "source_retrieved_at": retrieved_at,
                }
            )
            sequence += 1

    if not chunks:
        raise RuntimeError(
            "No text could be extracted from the PDF. Confirm that you downloaded the "
            "official text-based Guide to the NQF PDF rather than a web shortcut."
        )
    return chunks


def _write_corpus(*, chunks: list[dict], output: Path, snapshot: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    DEFAULT_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_SNAPSHOT.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"\nWrote {len(chunks)} chunks -> {output}")
    print(f"Snapshot -> {DEFAULT_SNAPSHOT}")


def ingest_pdf(pdf_path: Path, output: Path) -> None:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise SystemExit(f"Expected a .pdf file, got: {pdf_path}")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    print(f"Building policy corpus from local official Guide PDF...")
    print(f"PDF: {pdf_path}")
    chunks = build_pdf_chunks(pdf_path, retrieved_at)
    snapshot = {
        "built_at": retrieved_at,
        "ingestion_mode": "local_official_pdf",
        "publisher": "Australian Children's Education & Care Quality Authority (ACECQA)",
        "source_count": 1,
        "chunk_count": len(chunks),
        "sources": [
            {
                "source_id": GUIDE_PDF_SOURCE["source_id"],
                "source_title": GUIDE_PDF_SOURCE["title"],
                "source_url": GUIDE_PDF_SOURCE["url"],
                "local_filename": pdf_path.name,
                "chunk_count": len(chunks),
            }
        ],
    }
    _write_corpus(chunks=chunks, output=output, snapshot=snapshot)


def ingest_html(manifest_path: Path, output: Path, selected_sources: list[str]) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = manifest["sources"]
    if selected_sources:
        wanted = set(selected_sources)
        selected = [item for item in selected if item["source_id"] in wanted]
        missing = wanted - {item["source_id"] for item in selected}
        if missing:
            raise SystemExit(f"Unknown source_id(s): {', '.join(sorted(missing))}")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    all_chunks: list[dict] = []
    source_summary: list[dict] = []

    print(f"Building policy corpus from {len(selected)} official ACECQA HTML source(s)...")
    for index, source in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {source['source_id']} -> {source['url']}")
        html = fetch_html(source["url"])
        chunks = build_source_chunks(source, html, retrieved_at)
        if not chunks:
            raise RuntimeError(f"No usable content extracted from {source['url']}")
        all_chunks.extend(chunks)
        source_summary.append({"source_id": source["source_id"], "chunk_count": len(chunks)})
        print(f"  {len(chunks)} chunks")

    snapshot = {
        "built_at": retrieved_at,
        "ingestion_mode": "html",
        "manifest_version": manifest.get("version"),
        "publisher": manifest.get("publisher"),
        "source_count": len(selected),
        "chunk_count": len(all_chunks),
        "sources": source_summary,
    }
    _write_corpus(chunks=all_chunks, output=output, snapshot=snapshot)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build curated ACECQA policy corpus")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", action="append", default=[], help="Only ingest this HTML source_id (repeatable)")
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Recommended: local ACECQA Guide to the NQF PDF downloaded in a normal browser",
    )
    args = parser.parse_args()

    if args.pdf is not None:
        ingest_pdf(args.pdf, args.output)
        return

    try:
        ingest_html(args.manifest, args.output, args.source)
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        print(
            "\nRecommended recovery:\n"
            "1. Open ACECQA's Guide to the NQF page in Safari/Chrome.\n"
            "2. Click the official Full version PDF download.\n"
            "3. Run: python scripts/ingest_policy.py --pdf ~/Downloads/<downloaded-file>.pdf\n",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
