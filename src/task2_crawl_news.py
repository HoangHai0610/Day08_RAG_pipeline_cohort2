"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import html
import re
import json
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Điền danh sách URL bài báo cần crawl
ARTICLE_URLS = [
    "https://www.nguoiduatin.vn/khoi-to-bat-tam-giam-ca-si-chi-dan-nguoi-mau-andrea-aybar-204241114125017564.htm",
    "https://tienphong.vn/ca-si-chu-bin-truoc-khi-bi-bat-post1644204.tpo",
    "https://vnexpress.net/nguoi-mau-nhikolai-dinh-bi-bat-vi-tang-tru-ma-tuy-4762598.html",
    "https://nld.com.vn/phap-luat/bat-giam-dien-vien-huu-tin-vi-lien-quan-ma-tuy-20220617202258452.htm",
    "https://thanhnien.vn/ca-si-chau-viet-cuong-bi-dieu-tra-hanh-vi-vo-y-lam-chet-nguoi-185738249.htm",
]


class SimpleArticleParser(HTMLParser):
    """Trích title, publish date và text chính từ HTML báo điện tử."""

    CONTENT_TAGS = {"h1", "h2", "h3", "p", "li"}
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.published_time = ""
        self._in_title = False
        self._skip_depth = 0
        self._capture_tag = None
        self._buffer = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return

        if tag == "title":
            self._in_title = True
            return

        if tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            content = attrs.get("content", "").strip()
            if content and key in {"og:title", "twitter:title"} and not self.title:
                self.title = html.unescape(content)
            if content and key in {"article:published_time", "pubdate", "date"}:
                self.published_time = html.unescape(content)
            return

        if tag == "time" and attrs.get("datetime") and not self.published_time:
            self.published_time = html.unescape(attrs["datetime"].strip())

        if tag in self.CONTENT_TAGS and self._skip_depth == 0:
            self._capture_tag = tag
            self._buffer = []

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return

        if tag == "title":
            self._in_title = False
            return

        if tag == self._capture_tag:
            text = normalize_text(" ".join(self._buffer))
            if len(text) >= 40 and not is_boilerplate(text):
                self.parts.append(text)
            self._capture_tag = None
            self._buffer = []

    def handle_data(self, data):
        if self._skip_depth:
            return

        if self._in_title and not self.title:
            self.title = normalize_text(data)
            return

        if self._capture_tag:
            self._buffer.append(data)


def normalize_text(text: str) -> str:
    """Chuẩn hóa khoảng trắng để markdown sạch hơn."""
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def is_boilerplate(text: str) -> bool:
    """Bỏ một số đoạn điều hướng/quảng cáo thường gặp trên trang tin."""
    lowered = text.lower()
    boilerplate_markers = [
        "đăng nhập",
        "chia sẻ",
        "theo dõi",
        "bấm để",
        "quảng cáo",
        "hotline",
        "copyright",
        "liên hệ quảng cáo",
        "vui lòng nhập",
    ]
    return any(marker in lowered for marker in boilerplate_markers)


def fetch_article(url: str) -> dict:
    """Tải HTML và chuyển nội dung bài báo sang markdown đơn giản."""
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    parser = SimpleArticleParser()
    parser.feed(response.text)

    title = normalize_text(parser.title) or "Unknown"
    content = "\n\n".join(dict.fromkeys(parser.parts))
    if not content:
        content = normalize_text(response.text)

    return {
        "url": url,
        "title": title,
        "published_time": parser.published_time,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": f"# {title}\n\n{content}",
    }


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    return await asyncio.to_thread(fetch_article, url)


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        if filepath.exists() and filepath.stat().st_size > 500:
            print(f"[{i}/{len(ARTICLE_URLS)}] Skipping existing: {filepath}")
            continue

        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        try:
            article = await crawl_article(url)
        except Exception as exc:
            print(f"  Error: {exc}")
            continue

        # Lưu file JSON
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("Hay dien ARTICLE_URLS truoc khi chay!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
