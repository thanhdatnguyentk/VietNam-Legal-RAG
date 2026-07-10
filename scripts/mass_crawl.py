"""Mass crawler for Vietnamese legal documents from vanban.chinhphu.vn.

This script uses Playwright (headless Chromium) to crawl legal documents
because the target sites render content via JavaScript.

Usage:
    python scripts/mass_crawl.py --target 5000 --workers 3
    python scripts/mass_crawl.py --resume  # Resume from last checkpoint

Output:
    data/raw/<domain>/<doc_number>.txt       — Full text
    data/raw/<domain>/<doc_number>.meta.json — Metadata sidecar
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Mass crawl Vietnamese legal documents.")
console = Console()

# ── Paths ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKPOINT_FILE = PROJECT_ROOT / "data" / ".crawl_checkpoint.json"

# ── Domain classification ────────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "giao_thong": ["giao thông", "đường bộ", "lái xe", "phương tiện", "tốc độ", "đường sắt"],
    "hinh_su": ["hình sự", "tội phạm", "truy tố", "phạt tù", "khởi tố"],
    "dan_su": ["dân sự", "hợp đồng", "bồi thường", "thừa kế", "hôn nhân", "gia đình"],
    "lao_dong": ["lao động", "tiền lương", "bảo hiểm xã hội", "người lao động", "nghỉ phép"],
    "dat_dai": ["đất đai", "quyền sử dụng đất", "bất động sản", "nhà ở"],
    "doanh_nghiep": ["doanh nghiệp", "công ty", "cổ phần", "kinh doanh", "thương mại"],
    "thue": ["thuế", "thu nhập", "giá trị gia tăng", "hải quan", "xuất nhập khẩu"],
    "hanh_chinh": ["hành chính", "xử phạt", "vi phạm hành chính", "thẩm quyền"],
    "giao_duc": ["giáo dục", "đào tạo", "trường học", "sinh viên", "học sinh"],
    "y_te": ["y tế", "bệnh viện", "dược", "khám chữa bệnh", "bảo hiểm y tế"],
}


def classify_domain(title: str, body: str) -> str:
    """Classify a document into a legal domain based on title + body keywords."""
    text = (title + " " + body[:2000]).lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "khac"


def safe_filename(text: str, max_len: int = 80) -> str:
    """Create a filesystem-safe filename."""
    text = text.replace("/", "_").replace("\\", "_").replace(" ", "_")
    text = re.sub(r'[<>:"|?*]', "", text)
    text = text[:max_len].rstrip("._")
    return text or "unknown"


@dataclass
class CrawlCheckpoint:
    """Track crawling progress for resume capability."""
    crawled_ids: list[int] = field(default_factory=list)
    failed_ids: list[int] = field(default_factory=list)
    total_saved: int = 0
    last_page: int = 0

    def save(self, path: Path = CHECKPOINT_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = CHECKPOINT_FILE) -> "CrawlCheckpoint":
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        return cls()


def extract_doc_ids_from_listing(page, url: str) -> list[dict]:
    """Extract document IDs and metadata from a listing page."""
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(1)

    docs = []
    # Find document links with docid parameter
    links = page.query_selector_all("a[href*='docid=']")
    for link in links:
        href = link.get_attribute("href") or ""
        match = re.search(r"docid=(\d+)", href)
        if match:
            doc_id = int(match.group(1))
            title = link.inner_text().strip()
            if doc_id and title and len(title) > 5:
                docs.append({"id": doc_id, "title": title, "url": href})

    # Deduplicate by ID
    seen = set()
    unique = []
    for d in docs:
        if d["id"] not in seen:
            seen.add(d["id"])
            unique.append(d)

    return unique


def extract_document_content(page, doc_id: int) -> Optional[dict]:
    """Extract full content of a legal document using Playwright."""
    url = f"https://vanban.chinhphu.vn/?pageid=27160&docid={doc_id}"

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Extract title
        title = ""
        for selector in ["h1", ".doc-title", ".title-vb"]:
            el = page.query_selector(selector)
            if el:
                title = el.inner_text().strip()
                if title:
                    break
        if not title:
            title = page.title()

        # Extract document number from page content
        full_text = page.inner_text("body")
        doc_number = None
        # Pattern: "Số: 100/2019/NĐ-CP" or similar
        num_match = re.search(r"Số[:\s]+(\d+[\w/\-]+)", full_text[:3000])
        if num_match:
            doc_number = num_match.group(1).strip()

        # Extract main body text - try to get the document content area
        body = ""
        for selector in [
            "div.fulltext",
            "div.content-vb",
            "div.box-ct",
            "div.content1",
            "div[class*='noidung']",
            "div[class*='content']",
            "article",
            "main",
        ]:
            el = page.query_selector(selector)
            if el:
                text = el.inner_text().strip()
                if len(text) > 200 and ("Điều" in text or "Chương" in text):
                    body = text
                    break

        # Fallback: get body text and try to extract the legal content
        if not body or len(body) < 200:
            body = full_text
            # Try to trim navigation/header/footer
            start = 0
            for marker in ["Chương I", "Chương 1", "CHƯƠNG I", "Điều 1"]:
                idx = body.find(marker)
                if idx > 0:
                    start = idx
                    break
            if start > 0:
                body = body[start:]

        if not body or len(body) < 100:
            return None

        # Extract dates
        issued_date = None
        date_match = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", full_text[:3000])
        if date_match:
            d, m, y = date_match.group(1), date_match.group(2), date_match.group(3)
            issued_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

        # Classify domain
        domain = classify_domain(title, body)

        # Extract document type
        doc_type = "Không rõ"
        for dtype in ["Luật", "Nghị định", "Thông tư", "Quyết định", "Nghị quyết",
                       "Chỉ thị", "Công văn", "Thông báo", "Pháp lệnh", "Lệnh"]:
            if dtype.lower() in title.lower():
                doc_type = dtype
                break

        return {
            "id": doc_id,
            "url": url,
            "title": title,
            "document_number": doc_number,
            "issued_date": issued_date,
            "domain": domain,
            "document_type": doc_type,
            "body_text": body,
        }

    except Exception as e:
        logger.warning("Failed to extract doc %d: %s", doc_id, e)
        return None


def save_document(doc: dict, base_dir: Path = RAW_DIR) -> Path:
    """Save a document as .txt + .meta.json pair."""
    domain = doc.get("domain", "khac")
    domain_dir = base_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    doc_num = doc.get("document_number")
    if doc_num:
        fname = safe_filename(doc_num)
    else:
        fname = safe_filename(doc.get("title", str(doc["id"])))[:60]
        fname = f"{fname}_{doc['id']}"

    txt_path = domain_dir / f"{fname}.txt"
    meta_path = domain_dir / f"{fname}.meta.json"

    # Avoid overwriting
    if txt_path.exists():
        txt_path = domain_dir / f"{fname}_{doc['id']}.txt"
        meta_path = domain_dir / f"{fname}_{doc['id']}.meta.json"

    # Write body text
    txt_path.write_text(doc["body_text"], encoding="utf-8")

    # Write metadata
    meta = {
        "url": doc["url"],
        "title": doc["title"],
        "document_number": doc.get("document_number"),
        "issued_date": doc.get("issued_date"),
        "domain": doc["domain"],
        "extra_metadata": {
            "document_type": doc.get("document_type", ""),
            "source": "vanban.chinhphu.vn",
            "crawl_id": doc["id"],
        },
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return txt_path


@app.command()
def crawl(
    target: int = typer.Option(5000, "--target", "-t", help="Target number of documents to crawl"),
    resume: bool = typer.Option(False, "--resume", help="Resume from last checkpoint"),
    start_id: int = typer.Option(1, "--start-id", help="Starting document ID"),
    end_id: int = typer.Option(220000, "--end-id", help="Ending document ID"),
    batch_size: int = typer.Option(50, "--batch-size", help="Documents per batch before checkpoint"),
    delay: float = typer.Option(0.5, "--delay", help="Delay between requests in seconds"),
) -> None:
    """Crawl Vietnamese legal documents from vanban.chinhphu.vn."""
    from playwright.sync_api import sync_playwright

    console.print("[bold]🏛️ Vietnam Legal RAG — Mass Crawler[/bold]")
    console.print(f"Target:     {target} documents")
    console.print(f"ID range:   {start_id} → {end_id}")
    console.print(f"Delay:      {delay}s between requests")
    console.print(f"Output:     {RAW_DIR}")
    console.print()

    # Load or create checkpoint
    checkpoint = CrawlCheckpoint.load() if resume else CrawlCheckpoint()
    crawled_set = set(checkpoint.crawled_ids)
    failed_set = set(checkpoint.failed_ids)

    if resume:
        console.print(f"[yellow]Resuming: {checkpoint.total_saved} saved, "
                      f"{len(crawled_set)} crawled, {len(failed_set)} failed[/yellow]")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        # Strategy 1: Crawl listing pages to discover doc IDs
        console.print("[bold blue]Phase 1: Discovering document IDs from listing pages...[/bold blue]")
        all_doc_ids = set()

        try:
            for p in range(1, 500):  # Up to 500 listing pages
                listing_url = f"https://vanban.chinhphu.vn/?pageid=27160&p={p}"
                try:
                    docs = extract_doc_ids_from_listing(page, listing_url)
                    if not docs:
                        logger.info("No more docs at page %d, stopping discovery", p)
                        break
                    for d in docs:
                        all_doc_ids.add(d["id"])
                    logger.info("Page %d: found %d docs (total unique: %d)", p, len(docs), len(all_doc_ids))

                    if len(all_doc_ids) >= target * 2:  # Get enough candidates
                        break
                    time.sleep(delay)
                except Exception as e:
                    logger.warning("Failed listing page %d: %s", p, e)
                    continue
        except KeyboardInterrupt:
            console.print("\n[yellow]Discovery interrupted. Proceeding with found IDs.[/yellow]")

        # Strategy 2: Also try sequential ID scanning for more coverage
        if len(all_doc_ids) < target:
            console.print(f"[blue]Adding sequential IDs {start_id}-{end_id} for broader coverage...[/blue]")
            for i in range(end_id, max(start_id - 1, end_id - target * 3), -1):
                all_doc_ids.add(i)
                if len(all_doc_ids) >= target * 3:
                    break

        # Remove already crawled
        remaining_ids = sorted(all_doc_ids - crawled_set - failed_set, reverse=True)
        console.print(f"\n[bold green]Phase 2: Crawling {len(remaining_ids)} candidate documents[/bold green]")
        console.print(f"Target: {target - checkpoint.total_saved} remaining\n")

        saved_count = checkpoint.total_saved
        batch_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Crawling...",
                total=min(target, len(remaining_ids)),
            )

            for doc_id in remaining_ids:
                if saved_count >= target:
                    break

                try:
                    doc = extract_document_content(page, doc_id)
                    crawled_set.add(doc_id)

                    if doc and len(doc.get("body_text", "")) > 200:
                        path = save_document(doc)
                        saved_count += 1
                        batch_count += 1
                        progress.update(task, advance=1,
                                       description=f"[green]✓ {doc['domain']}/{path.stem[:30]}[/green]")
                    else:
                        failed_set.add(doc_id)
                        progress.update(task, advance=1,
                                       description=f"[dim]Skip ID {doc_id}[/dim]")

                    time.sleep(delay)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Interrupted! Saving checkpoint...[/yellow]")
                    break
                except Exception as e:
                    failed_set.add(doc_id)
                    logger.debug("Error on ID %d: %s", doc_id, e)
                    progress.update(task, advance=1)

                # Save checkpoint periodically
                if batch_count >= batch_size:
                    checkpoint.crawled_ids = list(crawled_set)
                    checkpoint.failed_ids = list(failed_set)
                    checkpoint.total_saved = saved_count
                    checkpoint.save()
                    batch_count = 0
                    logger.info("Checkpoint saved: %d documents", saved_count)

        browser.close()

    # Final checkpoint
    checkpoint.crawled_ids = list(crawled_set)
    checkpoint.failed_ids = list(failed_set)
    checkpoint.total_saved = saved_count
    checkpoint.save()

    # Print summary
    console.print(f"\n[bold green]{'='*50}[/bold green]")
    console.print(f"[bold]Crawling Complete![/bold]")
    console.print(f"  Total saved:    {saved_count}")
    console.print(f"  Total crawled:  {len(crawled_set)}")
    console.print(f"  Failed/skipped: {len(failed_set)}")

    # Count by domain
    domain_counts = {}
    for domain_dir in RAW_DIR.iterdir():
        if domain_dir.is_dir() and domain_dir.name != ".gitkeep":
            count = len(list(domain_dir.glob("*.txt")))
            if count > 0:
                domain_counts[domain_dir.name] = count

    if domain_counts:
        console.print(f"\n  [bold]By domain:[/bold]")
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            console.print(f"    {domain}: {count}")

    console.print(f"\n  Resume with: python scripts/mass_crawl.py --resume")


if __name__ == "__main__":
    app()
