"""Import Vietnamese legal documents from HuggingFace dataset.

Downloads and processes the th1nhng0/vietnamese-legal-documents dataset,
converting HTML content to plain text and saving in the project's
standard .txt + .meta.json format.

Usage:
    python scripts/import_hf_dataset.py --limit 5000
    python scripts/import_hf_dataset.py --limit 5000 --min-length 500
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import typer
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Import legal docs from HuggingFace.")
console = Console()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Domain classification keywords
DOMAIN_KEYWORDS = {
    "giao_thong": [
        "giao thông", "đường bộ", "lái xe", "phương tiện", "tốc độ",
        "đường sắt", "giấy phép lái xe", "gplx", "nồng độ cồn",
    ],
    "hinh_su": [
        "hình sự", "tội phạm", "truy tố", "phạt tù", "khởi tố",
        "bộ luật hình sự", "tạm giam", "điều tra",
    ],
    "dan_su": [
        "dân sự", "hợp đồng", "bồi thường", "thừa kế", "hôn nhân",
        "gia đình", "quyền sở hữu", "tài sản",
    ],
    "lao_dong": [
        "lao động", "tiền lương", "bảo hiểm xã hội", "người lao động",
        "nghỉ phép", "hợp đồng lao động", "sa thải", "công đoàn",
    ],
    "dat_dai": [
        "đất đai", "quyền sử dụng đất", "bất động sản", "nhà ở",
        "xây dựng", "quy hoạch", "giải phóng mặt bằng",
    ],
    "doanh_nghiep": [
        "doanh nghiệp", "công ty", "cổ phần", "kinh doanh", "thương mại",
        "đầu tư", "phá sản", "giải thể",
    ],
    "thue": [
        "thuế", "thu nhập", "giá trị gia tăng", "hải quan",
        "xuất nhập khẩu", "ngân sách", "tài chính",
    ],
    "hanh_chinh": [
        "hành chính", "xử phạt vi phạm", "thẩm quyền", "cán bộ",
        "công chức", "viên chức", "thủ tục hành chính",
    ],
    "giao_duc": [
        "giáo dục", "đào tạo", "trường học", "sinh viên", "học sinh",
        "đại học", "cao đẳng", "nghề",
    ],
    "y_te": [
        "y tế", "bệnh viện", "dược", "khám chữa bệnh",
        "bảo hiểm y tế", "vệ sinh", "an toàn thực phẩm",
    ],
    "moi_truong": [
        "môi trường", "ô nhiễm", "bảo vệ môi trường", "chất thải",
        "tài nguyên", "khoáng sản", "nước",
    ],
}


def classify_domain(title: str, body: str) -> str:
    """Classify a document into a legal domain."""
    text = (title + " " + body[:3000]).lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "khac"


def html_to_text(html: str) -> str:
    """Convert HTML content to clean plain text."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "head"]):
        tag.decompose()

    # Get text
    text = soup.get_text("\n", strip=True)

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def extract_metadata_from_text(text: str) -> dict:
    """Extract document metadata from the body text."""
    meta = {}

    # Document number: "Số: 100/2019/NĐ-CP"
    num_match = re.search(r"Số[:\s]+(\d+[\w/\-\.]+)", text[:2000])
    if num_match:
        meta["document_number"] = num_match.group(1).strip()

    # Document type
    for dtype in ["Luật", "Bộ luật", "Nghị định", "Thông tư", "Quyết định",
                   "Nghị quyết", "Chỉ thị", "Công văn", "Pháp lệnh", "Sắc lệnh"]:
        if dtype.lower() in text[:3000].lower():
            meta["document_type"] = dtype
            break

    # Date: "ngày X tháng Y năm Z"
    date_match = re.search(
        r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
        text[:3000],
    )
    if date_match:
        d, m, y = date_match.group(1), date_match.group(2), date_match.group(3)
        meta["issued_date"] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

    # Issuer
    for issuer_pattern in [
        r"(QUỐC HỘI|CHÍNH PHỦ|THỦ TƯỚNG CHÍNH PHỦ|BỘ [A-ZĐ\s]+)",
    ]:
        issuer_match = re.search(issuer_pattern, text[:1000])
        if issuer_match:
            meta["issuer"] = issuer_match.group(1).strip()
            break

    return meta


def safe_filename(text: str, max_len: int = 80) -> str:
    """Create a safe filename."""
    text = text.replace("/", "_").replace("\\", "_").replace(" ", "_")
    text = re.sub(r'[<>:"|?*\n\r]', "", text)
    return text[:max_len].rstrip("._") or "unknown"


@app.command()
def main(
    limit: int = typer.Option(5000, "--limit", "-n", help="Max documents to import"),
    min_length: int = typer.Option(500, "--min-length", help="Min text length (chars) to include"),
    max_length: int = typer.Option(500000, "--max-length", help="Max text length to include"),
    out_dir: Path = typer.Option(RAW_DIR, "--out-dir"),
) -> None:
    """Import legal documents from HuggingFace dataset."""
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    console.print("[bold]🏛️ Vietnam Legal RAG — HuggingFace Importer[/bold]")
    console.print(f"Target:      {limit} documents")
    console.print(f"Min length:  {min_length} chars")
    console.print(f"Output:      {out_dir}")
    console.print()

    # Step 1: Download content + metadata
    console.print("[blue]Downloading dataset from HuggingFace...[/blue]")
    content_path = hf_hub_download(
        repo_id="th1nhng0/vietnamese-legal-documents",
        filename="data/content.parquet",
        repo_type="dataset",
    )
    metadata_path = hf_hub_download(
        repo_id="th1nhng0/vietnamese-legal-documents",
        filename="data/metadata.parquet",
        repo_type="dataset",
    )
    console.print("[green]✓ Dataset downloaded[/green]")

    # Step 2: Load data
    console.print("[blue]Loading parquet files...[/blue]")
    content_table = pq.read_table(content_path)
    metadata_table = pq.read_table(metadata_path)

    console.print(f"  Content:  {content_table.num_rows:,} rows")
    console.print(f"  Metadata: {metadata_table.num_rows:,} rows")

    # Build metadata lookup by ID
    meta_dict = {}
    meta_data = metadata_table.to_pydict()
    for i in range(metadata_table.num_rows):
        doc_id = str(meta_data["id"][i])
        meta_dict[doc_id] = {
            "title": meta_data.get("title", [None])[i],
            "so_ky_hieu": meta_data.get("so_ky_hieu", [None])[i],
            "ngay_ban_hanh": meta_data.get("ngay_ban_hanh", [None])[i],
            "loai_van_ban": meta_data.get("loai_van_ban", [None])[i],
            "co_quan_ban_hanh": meta_data.get("co_quan_ban_hanh", [None])[i],
            "linh_vuc": meta_data.get("linh_vuc", [None])[i],
            "tinh_trang_hieu_luc": meta_data.get("tinh_trang_hieu_luc", [None])[i],
        }
    console.print(f"  Metadata index: {len(meta_dict):,} entries")

    # Step 3: Process and save
    console.print(f"\n[blue]Processing documents...[/blue]")
    saved = 0
    skipped_short = 0
    skipped_long = 0
    skipped_empty = 0
    domain_counts: dict[str, int] = {}

    # Read content in batches for memory efficiency
    content_ids = content_table.column("id").to_pylist()
    content_htmls = content_table.column("content_html").to_pylist()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Importing...", total=min(limit, len(content_ids)))

        for i in range(len(content_ids)):
            if saved >= limit:
                break

            doc_id = str(content_ids[i])
            html = content_htmls[i]

            if not html:
                skipped_empty += 1
                continue

            # Convert HTML to text
            text = html_to_text(html)

            if len(text) < min_length:
                skipped_short += 1
                continue
            if len(text) > max_length:
                skipped_long += 1
                continue

            # Get metadata
            meta = meta_dict.get(doc_id, {})
            title = meta.get("title") or ""

            # Extract additional metadata from text
            text_meta = extract_metadata_from_text(text)
            doc_number = meta.get("so_ky_hieu") or text_meta.get("document_number") or ""

            # Classify domain
            domain = classify_domain(title, text)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            # Generate filename
            if doc_number:
                fname = safe_filename(doc_number)
            else:
                fname = safe_filename(title[:60]) if title else f"doc_{doc_id}"

            # Save
            domain_dir = out_dir / domain
            domain_dir.mkdir(parents=True, exist_ok=True)

            txt_path = domain_dir / f"{fname}.txt"
            if txt_path.exists():
                txt_path = domain_dir / f"{fname}_{doc_id}.txt"

            meta_path = txt_path.with_suffix(".meta.json")

            # Parse date
            issued_date = meta.get("ngay_ban_hanh")
            if issued_date and "/" in issued_date:
                parts = issued_date.split("/")
                if len(parts) == 3:
                    issued_date = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

            # Write files
            txt_path.write_text(text, encoding="utf-8")
            sidecar = {
                "url": f"https://vbpl.vn/van-ban/{doc_id}",
                "title": title,
                "document_number": doc_number,
                "issued_date": issued_date,
                "domain": domain,
                "extra_metadata": {
                    "document_type": meta.get("loai_van_ban") or text_meta.get("document_type", ""),
                    "issuer": meta.get("co_quan_ban_hanh") or text_meta.get("issuer", ""),
                    "status": meta.get("tinh_trang_hieu_luc") or "",
                    "field": meta.get("linh_vuc") or "",
                    "source": "th1nhng0/vietnamese-legal-documents",
                    "original_id": doc_id,
                },
            }
            meta_path.write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            saved += 1
            progress.update(
                task, advance=1,
                description=f"[green]{domain}/{txt_path.stem[:30]}[/green]",
            )

    # Print summary
    console.print(f"\n[bold green]{'='*50}[/bold green]")
    console.print(f"[bold]Import Complete![/bold]")
    console.print(f"  Documents saved:    {saved:,}")
    console.print(f"  Skipped (short):    {skipped_short:,}")
    console.print(f"  Skipped (long):     {skipped_long:,}")
    console.print(f"  Skipped (empty):    {skipped_empty:,}")

    # Domain breakdown
    table = Table(title="\n📊 Documents by Domain")
    table.add_column("Domain", style="cyan")
    table.add_column("Count", justify="right", style="green")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        table.add_row(domain, f"{count:,}")
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{saved:,}[/bold]")
    console.print(table)

    console.print(f"\n  Next: python scripts/mass_ingest.py --stats")


if __name__ == "__main__":
    app()
