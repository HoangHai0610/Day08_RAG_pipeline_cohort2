"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install markitdown

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

LEGAL_EXTENSIONS = {".pdf", ".docx", ".doc"}


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()
    converted = []

    if not legal_dir.exists():
        print(f"Missing directory: {legal_dir}")
        return converted

    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() not in LEGAL_EXTENSIONS:
            continue

        print(f"Converting legal: {filepath.name}")
        result = md.convert(str(filepath))
        text = (getattr(result, "text_content", "") or "").strip()

        if not text:
            raise ValueError(f"Converted content is empty: {filepath}")

        header = (
            f"# {filepath.stem}\n\n"
            f"**Source file:** {filepath.name}\n"
            f"**Document type:** legal\n\n"
            "---\n\n"
        )
        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(header + text, encoding="utf-8")
        converted.append(output_path)
        print(f"  Saved: {output_path}")

    return converted


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted = []

    if not news_dir.exists():
        print(f"Missing directory: {news_dir}")
        return converted

    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() != ".json":
            continue

        print(f"Converting news: {filepath.name}")
        data = json.loads(filepath.read_text(encoding="utf-8"))
        title = data.get("title") or filepath.stem
        content_markdown = (data.get("content_markdown") or "").strip()

        if not content_markdown:
            raise ValueError(f"JSON article has no content_markdown: {filepath}")

        header = (
            f"# {title}\n\n"
            f"**Source:** {data.get('url', 'N/A')}\n"
            f"**Published:** {data.get('published_time', 'N/A')}\n"
            f"**Crawled:** {data.get('date_crawled', 'N/A')}\n"
            f"**Document type:** news\n\n"
            "---\n\n"
        )

        # Nếu crawler đã thêm H1, bỏ heading trùng để markdown gọn hơn.
        first_line = content_markdown.splitlines()[0].strip() if content_markdown.splitlines() else ""
        if first_line == f"# {title}":
            content_markdown = "\n".join(content_markdown.splitlines()[1:]).strip()

        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(header + content_markdown + "\n", encoding="utf-8")
        converted.append(output_path)
        print(f"  Saved: {output_path}")

    return converted


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\nDone. Output:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
