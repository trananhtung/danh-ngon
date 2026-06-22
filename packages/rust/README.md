# danh-ngon

> Kho **danh ngôn song ngữ Việt–Anh** với hơn **9.000 câu**, nhúng sẵn trong crate — không cần kết nối mạng, không cần tệp ngoài.

[![crates.io](https://img.shields.io/crates/v/danh-ngon.svg)](https://crates.io/crates/danh-ngon)
[![docs.rs](https://docs.rs/danh-ngon/badge.svg)](https://docs.rs/danh-ngon)

Phù hợp cho: CLI "danh ngôn mỗi ngày", bot, dịch vụ web, ứng dụng nhúng, công cụ học tiếng Anh…

## Tính năng

- 📚 **9.000+ danh ngôn** kèm bản dịch tiếng Anh và tên tác giả.
- 🏷️ **18 chủ đề**: cuộc sống, tình yêu, thành công, giáo dục, thời gian, sự nghiệp…
- 🔍 **Tìm kiếm không dấu** (gõ `hanh phuc` vẫn ra `hạnh phúc`).
- 🎲 Lấy câu **ngẫu nhiên**, có thể lọc theo chủ đề/tác giả.
- ⚡ Dữ liệu nhúng bằng `include_str!`, phân tích **lazy** một lần; phụ thuộc tối thiểu (`serde`, `serde_json`).

## Cài đặt

```toml
[dependencies]
danh-ngon = "1"
```

Hoặc:

```bash
cargo add danh-ngon
```

## Bắt đầu nhanh

```rust
use danh_ngon::{random_quote, by_topic, search, random_quote_filtered};

fn main() {
    // Một câu ngẫu nhiên
    let q = random_quote();
    println!("\"{}\" — {}", q.vi, q.author);

    // Câu ngẫu nhiên thuộc chủ đề Tình yêu
    if let Some(q) = random_quote_filtered(Some("tinh-yeu"), None) {
        println!("{}", q.vi);
    }

    // Lọc theo chủ đề
    let danh_sach = by_topic("cuoc-song");
    println!("Có {} câu về cuộc sống", danh_sach.len());

    // Tìm kiếm không dấu
    let kq = search("thanh cong");
    println!("Tìm thấy {} câu", kq.len());
}
```

## Kiểu dữ liệu

```rust
pub struct Quote {
    pub id: u32,            // mã định danh ổn định
    pub vi: String,         // nội dung tiếng Việt
    pub en: String,         // bản tiếng Anh ("" nếu không có)
    pub author: String,     // tác giả ("Khuyết danh" nếu không rõ)
    pub topics: Vec<String> // các slug chủ đề
}
```

## API

| Hàm | Mô tả |
|-----|-------|
| `all_quotes() -> &'static [Quote]` | Toàn bộ danh ngôn. |
| `count() -> usize` | Tổng số câu. |
| `by_id(id) -> Option<&Quote>` | Lấy câu theo id. |
| `random_quote() -> &Quote` | Một câu ngẫu nhiên. |
| `random_quote_filtered(topic, author) -> Option<&Quote>` | Ngẫu nhiên có lọc. |
| `random_quotes(n) -> Vec<&Quote>` | `n` câu ngẫu nhiên, không trùng. |
| `by_author(name) -> Vec<&Quote>` | Lọc theo tác giả (không phân biệt dấu/hoa thường). |
| `by_topic(slug) -> Vec<&Quote>` | Lọc theo slug chủ đề. |
| `search(keyword) -> Vec<&Quote>` | Tìm trên VI/EN/tác giả, không phân biệt dấu. |
| `topics() -> &'static [Topic]` | Danh sách chủ đề kèm số lượng. |
| `authors(limit) -> Vec<(String, usize)>` | Tác giả kèm số lượng (`0` = tất cả). |
| `normalize(text) -> String` | Bỏ dấu + chữ thường (tiện ích). |

### Danh sách chủ đề (slug)

`cuoc-song`, `tinh-yeu`, `nhung-manh-ngon-tinh`, `su-nghiep`, `tieng-anh`,
`tinh-ban`, `song-chet`, `thoi-gian`, `trai-tim`, `giao-duc`, `yeu-nuoc`,
`tri-tue`, `tam-hon`, `van-minh-khoa-hoc`, `gia-dinh`, `thanh-cong`,
`trich-dan-hay`, `thay-doi`.

Gọi `topics()` để lấy nhãn tiếng Việt và số lượng chính xác.

## Ví dụ: CLI "Danh ngôn mỗi ngày"

```rust
use danh_ngon::random_quote_filtered;

fn main() {
    let q = random_quote_filtered(Some("cuoc-song"), None).unwrap();
    println!("🌅 {}\n   — {}\n   ({})", q.vi, q.author, q.en);
}
```

## Giấy phép

Mã nguồn phát hành theo giấy phép **MIT**. Dữ liệu tổng hợp từ kho danh ngôn cộng đồng.
