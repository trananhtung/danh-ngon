# 📚 danh-ngon — Kho danh ngôn song ngữ Việt–Anh

Hai thư viện dùng chung **một bộ dữ liệu** gồm hơn **9.000 câu danh ngôn** song ngữ
Việt–Anh, kèm tác giả và 18 chủ đề. Dữ liệu được **đóng gói sẵn** trong thư viện —
không cần mạng, không cần API key.

| Hệ sinh thái | Gói | Cài đặt |
|--------------|-----|---------|
| Node / JavaScript / TypeScript | [`danh-ngon`](https://www.npmjs.com/package/danh-ngon) (npm) | `npm install danh-ngon` |
| Rust | [`danh-ngon`](https://crates.io/crates/danh-ngon) (crate) | `cargo add danh-ngon` |

## Vì sao nên dùng?

- 📚 **9.000+ danh ngôn** đã khử trùng, kèm bản tiếng Anh và tên tác giả.
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
│   ├── quotes.json          # toàn bộ danh ngôn (đẹp, dễ đọc)
│   ├── quotes.min.json      # bản rút gọn (đóng gói vào thư viện)
│   ├── topics.json          # chủ đề + nhãn tiếng Việt + số lượng
│   ├── authors.json         # tác giả + số lượng
│   └── meta.json            # thống kê tổng quan
├── scripts/build_dataset.py # chuyển .xlsm -> JSON
├── packages/
│   ├── npm/                 # thư viện npm (TypeScript)
│   └── rust/                # crate Rust
├── docs/                    # tài liệu thiết kế
└── PUBLISHING.md            # hướng dẫn xuất bản
```

## Bộ dữ liệu

Dữ liệu được sinh từ file Excel nguồn bằng `scripts/build_dataset.py`:

```bash
python3 scripts/build_dataset.py
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
