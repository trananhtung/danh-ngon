# Kho danh ngôn đầy đủ (data/full/)

Thư mục này chứa **767.590+ câu danh ngôn** chia thành 16 file JSONL.
Các file `.jsonl` không được lưu trong git — tải về từ **GitHub Releases v2.0.0**
(`danh-ngon-full-v2.0.0.zip`).

## Cấu trúc file

```
data/full/
├── README.md           # file này
├── manifest.json       # danh sách file JSONL và số lượng
├── stats.json          # thống kê nhanh (top tác giả, chủ đề)
├── author_index.json   # top 5.000 tác giả + số câu
├── topic_index.json    # 18 chủ đề + số câu + vị trí mẫu
└── quotes_001.jsonl    # 50.000 câu/file  ← cần tải từ Releases
    quotes_002.jsonl
    ...
    quotes_016.jsonl
```

## Format mỗi dòng JSONL

```json
{"id":1,"en":"Be yourself; everyone else is already taken.","vi":"","author":"Oscar Wilde","topics":[]}
```

| Field | Mô tả |
|-------|-------|
| `id` | ID duy nhất |
| `en` | Tiếng Anh (luôn có) |
| `vi` | Tiếng Việt (có thể rỗng nếu chưa dịch) |
| `author` | Tên tác giả |
| `topics` | Danh sách slug chủ đề |

## Đọc nhanh bằng Python

```python
import json
from pathlib import Path

# Đọc tất cả
def iter_quotes(data_dir="data/full"):
    manifest = json.loads(Path(data_dir, "manifest.json").read_text())
    for entry in manifest:
        with open(Path(data_dir, entry["file"]), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

# Lọc theo tác giả
def quotes_by_author(author, data_dir="data/full"):
    author_lower = author.lower()
    for q in iter_quotes(data_dir):
        if author_lower in q["author"].lower():
            yield q

# Lấy ngẫu nhiên theo vị trí (random access)
import random
def random_quote(data_dir="data/full"):
    manifest = json.loads(Path(data_dir, "manifest.json").read_text())
    entry = random.choice(manifest)
    fpath = Path(data_dir, entry["file"])
    lines = [l for l in fpath.read_text().splitlines() if l.strip()]
    return json.loads(random.choice(lines))
```

## Sử dụng index files

```python
# Xem top tác giả
stats = json.loads(Path("data/full/stats.json").read_text())
for a in stats["top_authors"][:10]:
    print(f"{a['name']}: {a['count']} câu")

# Xem thống kê chủ đề
for t in stats["top_topics"]:
    print(f"{t['slug']}: {t['count']} câu")
```
