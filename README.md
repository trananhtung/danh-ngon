# 📚 danh-ngon — Kho danh ngôn song ngữ Việt–Anh

[![npm version](https://img.shields.io/npm/v/danh-ngon?label=npm&color=cb3837)](https://www.npmjs.com/package/danh-ngon)
[![crates.io](https://img.shields.io/crates/v/danh-ngon?label=crate&color=f74c00)](https://crates.io/crates/danh-ngon)
[![CI](https://github.com/trananhtung/danh-ngon/actions/workflows/ci.yml/badge.svg)](https://github.com/trananhtung/danh-ngon/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hai thư viện dùng chung **một bộ dữ liệu** gồm hơn **30.000 câu danh ngôn** song ngữ
Việt–Anh, kèm tác giả và 18 chủ đề. Kho đầy đủ chứa **767.590+ câu** từ khắp thế giới.
Dữ liệu được **đóng gói sẵn** trong thư viện — không cần mạng, không cần API key.

| Hệ sinh thái | Gói | Cài đặt |
|--------------|-----|---------|
| Node / JavaScript / TypeScript | [![npm](https://img.shields.io/npm/v/danh-ngon)](https://www.npmjs.com/package/danh-ngon) | `npm install danh-ngon` |
| Rust | [![crates.io](https://img.shields.io/crates/v/danh-ngon)](https://crates.io/crates/danh-ngon) | `cargo add danh-ngon` |

## Vì sao nên dùng?

- 📚 **31.000+ danh ngôn** song ngữ (Anh–Việt) đã khử trùng, kèm tên tác giả; **767.590+ câu** trong kho đầy đủ.
- 🌍 Thu thập từ **Wikiquote** (EN+VI), AZQuotes, GitHub datasets, HuggingFace và nhiều nguồn khác.
- 🏷️ **18 chủ đề**: cuộc sống, tình yêu, thành công, giáo dục, thời gian, sự nghiệp, gia đình…
- 🔍 **Tìm kiếm không dấu** (gõ `hanh phuc` vẫn ra `hạnh phúc`).
- 🎲 Lấy câu **ngẫu nhiên**, lọc theo chủ đề/tác giả.
- ⚡ **Offline hoàn toàn**, API hai thư viện **đồng nhất**.

## Ví dụ nhanh

**JavaScript/TypeScript**
```ts
import { randomQuote } from "danh-ngon";
const q = randomQuote({ topic: "cuoc-song" })!;
console.log(`"${q.vi}" — ${q.author}`);
```

**Rust**
```rust
use danh_ngon::random_quote_filtered;
let q = random_quote_filtered(Some("cuoc-song"), None).unwrap();
println!("\"{}\" — {}", q.vi, q.author);
```

## Cấu trúc kho mã

```
danh-ngon/
├── data/                    # Bộ dữ liệu JSON chuẩn hoá (nguồn chung)
│   ├── quotes.json          # 30.784 danh ngôn song ngữ Anh–Việt (thư viện)
│   ├── quotes.min.json      # bản rút gọn (đóng gói vào thư viện)
│   ├── topics.json          # chủ đề + nhãn tiếng Việt + số lượng
│   ├── authors.json         # tác giả + số lượng
│   ├── meta.json            # thống kê tổng quan
│   └── full/                # kho đầy đủ 767.590+ câu (JSONL, 16 file)
│       ├── manifest.json    # danh sách file và số lượng
│       ├── quotes_001.jsonl # 50.000 câu/file
│       └── ...
├── scripts/
│   ├── build_dataset.py     # chuyển .xlsm -> JSON
│   └── crawl_quotes.py      # crawler đa nguồn (Wikiquote, AZQuotes…)
├── packages/
│   ├── npm/                 # thư viện npm (TypeScript)
│   └── rust/                # crate Rust
├── docs/                    # tài liệu thiết kế
└── PUBLISHING.md            # hướng dẫn xuất bản
```

## Bộ dữ liệu

### Thư viện (`data/quotes.json`)

30.784 câu danh ngôn song ngữ Anh–Việt, crawl và dịch tự động từ nhiều nguồn:
Wikiquote (EN+VI), AZQuotes, GitHub datasets, HuggingFace và web scraping.

### Kho đầy đủ (`data/full/`)

767.590+ câu chia thành 16 file JSONL, mỗi file ~50.000 câu. Phần lớn là tiếng Anh
(từ English Wikiquote dump), các câu song ngữ tiếp tục được bổ sung qua các phiên bản sau.

Đọc kho đầy đủ bằng Python:

```python
import json
from pathlib import Path

for f in sorted(Path('data/full').glob('quotes_*.jsonl')):
    for line in f.read_text().splitlines():
        q = json.loads(line)
        # q = {"id": ..., "en": "...", "vi": "...", "author": "...", "topics": [...]}
```

Dữ liệu được sinh/cập nhật bằng `scripts/crawl_quotes.py`:

```bash
python3 scripts/crawl_quotes.py all
```

Mỗi câu có dạng:

```json
{ "id": 1, "vi": "…", "en": "…", "author": "…", "topics": ["cuoc-song"] }
```

Quy trình build: đọc tất cả sheet → khử trùng theo nội dung tiếng Việt →
gộp chủ đề từ tên sheet → làm sạch tác giả → sửa lỗi đảo cột Việt/Anh →
chuẩn hoá khuyết danh → xuất JSON tất định.

## Tài liệu chi tiết

- Thư viện npm: [`packages/npm/README.md`](packages/npm/README.md)
- Crate Rust: [`packages/rust/README.md`](packages/rust/README.md)
- Hướng dẫn xuất bản: [`PUBLISHING.md`](PUBLISHING.md)
- Thiết kế: [`docs/superpowers/specs/`](docs/superpowers/specs/)

## Giấy phép

[MIT](LICENSE). Dữ liệu tổng hợp từ kho danh ngôn cộng đồng, mời bạn tự do sử dụng.
