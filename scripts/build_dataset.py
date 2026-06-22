#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline chuyển kho danh ngôn từ `full danh ngon.xlsm` sang JSON chuẩn hoá.

Sinh ra trong thư mục data/:
  - quotes.json    : mảng các câu danh ngôn đã khử trùng, kèm chủ đề & tác giả
  - topics.json    : map slug chủ đề -> { label, count }
  - authors.json   : danh sách tác giả kèm số lượng câu (giảm dần)
  - meta.json      : thống kê tổng quan

Chạy:  python3 scripts/build_dataset.py
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict, OrderedDict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSM = ROOT / "full danh ngon.xlsm"
DATA_DIR = ROOT / "data"
SCHEMA_VERSION = 1

# Các sheet là CHỦ ĐỀ: slug -> nhãn tiếng Việt.
# Chỉ những sheet này mới đóng góp 'topics' cho câu danh ngôn.
TOPIC_SHEETS = {
    "thay-doi": "Thay đổi",
    "danh-ngon-cuoc-song": "Cuộc sống",
    "thanh-cong": "Thành công",
    "nhung-trich-dan-hay": "Trích dẫn hay",
    "nhung-manh-ngon-tinh": "Mảnh ngôn tình",
    "danh-ngon-yeu-nuoc": "Yêu nước",
    "danh-ngon-van-minh-khoa-hoc": "Văn minh & Khoa học",
    "danh-ngon-tinh-yeu": "Tình yêu",
    "danh-ngon-tam-hon": "Tâm hồn",
    "danh-ngon-trai-tim": "Trái tim",
    "danh-ngon-giao-duc": "Giáo dục",
    "danh-ngon-tieng-anh": "Tiếng Anh",
    "danh-ngon-tinh-ban": "Tình bạn",
    "danh-ngon-tri-tue": "Trí tuệ",
    "danh-ngon-thoi-gian": "Thời gian",
    "danh-ngon-su-nghiep": "Sự nghiệp",
    "danh-ngon-song-chet": "Sống & Chết",
    "danh-ngon-gia-dinh": "Gia đình",
}

# Bỏ qua hẳn các sheet này (rỗng hoặc không phải dữ liệu).
SKIP_SHEETS = {"FullDanhNgon"}


def topic_slug(sheet_name: str) -> str:
    """Slug ngắn gọn: bỏ tiền tố 'danh-ngon-' cho dễ dùng."""
    s = sheet_name
    if s.startswith("danh-ngon-"):
        s = s[len("danh-ngon-"):]
    return s


# Các biến thể chỉ "không rõ tác giả" -> chuẩn hoá về "Khuyết danh".
_ANON = {"khuyet danh", "vo danh", "suu tam", "unknown", "anonymous", "n/a", "..."}

VN_CHARS = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")


def has_vietnamese(text: str) -> bool:
    """True nếu chuỗi chứa ký tự đặc trưng tiếng Việt (dấu)."""
    return any(c in VN_CHARS for c in text.lower())


def clean_author(raw) -> str:
    """Gỡ tiền tố 'Tác giả:' và làm sạch khoảng trắng."""
    if raw is None:
        return "Khuyết danh"
    s = str(raw).strip()
    # Gỡ 'Tác giả:' / 'Tác giả' ở đầu (không phân biệt hoa thường).
    s = re.sub(r"^\s*t[áa]c\s*gi[ảa]\s*[:\-]?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return "Khuyết danh"
    # Chuẩn hoá các biến thể khuyết danh.
    if norm_key(s) in _ANON:
        return "Khuyết danh"
    return s


def clean_text(raw) -> str:
    if raw is None:
        return ""
    return re.sub(r"\s+", " ", str(raw)).strip()


def norm_key(text: str) -> str:
    """Khoá khử trùng: bỏ dấu, lower, gộp khoảng trắng, bỏ ký tự không chữ-số."""
    s = unicodedata.normalize("NFD", text)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main():
    if not XLSM.exists():
        sys.exit(f"Không tìm thấy file: {XLSM}")

    wb = openpyxl.load_workbook(XLSM, read_only=True, data_only=True)

    # khoá -> bản ghi gộp
    merged = OrderedDict()

    for ws in wb.worksheets:
        if ws.title in SKIP_SHEETS:
            continue
        slug = topic_slug(ws.title) if ws.title in TOPIC_SHEETS else None
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row:
                continue
            vi = clean_text(row[0] if len(row) > 0 else "")
            en = clean_text(row[1] if len(row) > 1 else "")
            author = clean_author(row[2] if len(row) > 2 else None)
            if not vi and not en:
                continue
            # Sửa lỗi đảo cột: nếu cột VI là tiếng Anh còn cột EN là tiếng Việt thì hoán đổi.
            if vi and en and not has_vietnamese(vi) and has_vietnamese(en):
                vi, en = en, vi
            # Khoá ưu tiên theo câu tiếng Việt; nếu rỗng thì dùng tiếng Anh.
            key = norm_key(vi) if vi else "en:" + norm_key(en)
            if not key:
                continue

            if key in merged:
                rec = merged[key]
                # Giữ bản en/author đầy đủ hơn.
                if len(en) > len(rec["en"]):
                    rec["en"] = en
                if rec["author"] in ("", "Khuyết danh") and author != "Khuyết danh":
                    rec["author"] = author
                if not rec["vi"] and vi:
                    rec["vi"] = vi
            else:
                rec = {"vi": vi, "en": en, "author": author, "_topics": set()}
                merged[key] = rec

            if slug:
                merged[key]["_topics"].add(slug)

    # Sắp xếp tất định: theo (chủ đề đầu tiên, câu vi) để build ổn định.
    records = list(merged.values())
    records.sort(key=lambda r: (sorted(r["_topics"])[:1] or [""], norm_key(r["vi"] or r["en"])))

    quotes = []
    topic_counts = defaultdict(int)
    author_counts = defaultdict(int)

    for i, r in enumerate(records, start=1):
        topics = sorted(r["_topics"])
        q = {
            "id": i,
            "vi": r["vi"],
            "en": r["en"],
            "author": r["author"],
            "topics": topics,
        }
        quotes.append(q)
        for t in topics:
            topic_counts[t] += 1
        author_counts[r["author"]] += 1

    # topics.json
    topics_out = OrderedDict()
    for slug_name, label in sorted(TOPIC_SHEETS.items(), key=lambda kv: kv[1]):
        sl = topic_slug(slug_name)
        topics_out[sl] = {"label": label, "count": topic_counts.get(sl, 0)}

    # authors.json — giảm dần theo số lượng
    authors_out = OrderedDict()
    for name, cnt in sorted(author_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        authors_out[name] = cnt

    meta = {
        "schemaVersion": SCHEMA_VERSION,
        "totalQuotes": len(quotes),
        "totalAuthors": len(author_counts),
        "totalTopics": len(topics_out),
        "withEnglish": sum(1 for q in quotes if q["en"]),
        "source": "full danh ngon.xlsm",
    }

    DATA_DIR.mkdir(exist_ok=True)
    _write(DATA_DIR / "quotes.json", quotes, pretty=True)
    _write(DATA_DIR / "quotes.min.json", quotes, pretty=False)
    _write(DATA_DIR / "topics.json", topics_out, pretty=True)
    _write(DATA_DIR / "authors.json", authors_out, pretty=True)
    _write(DATA_DIR / "meta.json", meta, pretty=True)

    print("Đã build xong:")
    for k, v in meta.items():
        print(f"  {k}: {v}")
    print(f"  Top chủ đề: {sorted(topics_out.items(), key=lambda kv: -kv[1]['count'])[:3]}")


def _write(path: Path, obj, pretty: bool):
    with path.open("w", encoding="utf-8") as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
