# Thiết kế: Thư viện danh ngôn song ngữ (npm + crate Rust)

**Ngày:** 2026-06-22
**Trạng thái:** Đã duyệt (chế độ tự chủ theo /goal)

## 1. Mục tiêu

Biến kho danh ngôn trong `full danh ngon.xlsm` thành hai thư viện dùng được ngay,
cho hai hệ sinh thái phổ biến nhất:

- **npm** (`danh-ngon`) — cho JavaScript/TypeScript (Node, Deno, trình duyệt qua bundler).
- **crate Rust** (`danh-ngon`) — cho ứng dụng Rust.

Cả hai chia sẻ **cùng một bộ dữ liệu JSON chuẩn hoá**, có API tương đương nhau,
tài liệu bằng tiếng Việt, và sẵn sàng publish lên GitHub / npm / crates.io.

## 2. Nguồn dữ liệu

File `full danh ngon.xlsm` gồm 35 sheet:

- 1 sheet rỗng (`FullDanhNgon`) → bỏ qua.
- ~18 sheet **chủ đề** (cuộc sống, thành công, tình yêu, giáo dục, thời gian,
  sự nghiệp, gia đình, tình bạn, trí tuệ, tâm hồn, trái tim, yêu nước,
  văn minh & khoa học, sống & chết, mảnh ngôn tình, thay đổi, trích dẫn hay, tiếng Anh).
- ~14 sheet **tác giả** (Hồ Chí Minh, Einstein, Voltaire, Victor Hugo, Aristotle,
  Camus, Franklin, Zig Ziglar, Tony Robbins, Jim Rohn, Napoleon Hill, Dale Carnegie,
  Brian Tracy, Emerson).
- Sheet tổng hợp (`tong-hop`) và khuyết danh (`khuyet-danh`).

Mỗi dòng: `Column1` = câu tiếng Việt, `Column2` = bản tiếng Anh, `Column3` = `"Tác giả: X"`.
Tổng ~9.325 dòng (có trùng lặp giữa `tong-hop` và các sheet chủ đề).

## 3. Định dạng dữ liệu chuẩn hoá

Pipeline `scripts/build_dataset.py` (Python + openpyxl) sinh ra `data/`:

### `quotes.json`
Mảng các đối tượng `Quote`:

```json
{
  "id": 1,
  "vi": "Câu tiếng Việt (đã trim).",
  "en": "English version or empty string.",
  "author": "Tên tác giả đã làm sạch (\"Tác giả: \" được gỡ bỏ).",
  "topics": ["cuoc-song", "thanh-cong"]
}
```

- **Khử trùng** theo khoá là câu tiếng Việt sau khi chuẩn hoá (lower + gộp khoảng trắng).
  Khi trùng: gộp danh sách `topics`, giữ bản `en`/`author` đầy đủ nhất.
- `topics` là slug, chỉ lấy từ các sheet **chủ đề** (không lấy tên sheet tác giả/tổng hợp).
- `author` lấy từ Column3; rỗng → `"Khuyết danh"`.
- `id` đánh số tuần tự, ổn định (sắp xếp theo topic rồi text để build có tính tất định).

### `topics.json`
Map slug → nhãn tiếng Việt + số lượng: `{ "cuoc-song": {"label":"Cuộc sống","count":1700} }`.

### `authors.json`
Map tên tác giả → số lượng câu, sắp theo số lượng giảm dần.

### `meta.json`
Thống kê: tổng số câu, số tác giả, số chủ đề, ngày build, phiên bản schema.

## 4. API (đồng nhất giữa hai thư viện)

| Chức năng            | npm (TS)                       | Rust                                  |
|----------------------|--------------------------------|---------------------------------------|
| Lấy tất cả           | `getAllQuotes()`               | `all_quotes()`                        |
| Ngẫu nhiên           | `randomQuote(opts?)`           | `random_quote()` / `random_quote_filtered()` |
| Theo tác giả         | `quotesByAuthor(name)`         | `by_author(name)`                     |
| Theo chủ đề          | `quotesByTopic(slug)`          | `by_topic(slug)`                      |
| Tìm từ khoá          | `search(keyword, opts?)`       | `search(keyword)`                     |
| Theo ID              | `getQuoteById(id)`             | `by_id(id)`                           |
| Liệt kê tác giả      | `listAuthors()`                | `authors()`                           |
| Liệt kê chủ đề       | `listTopics()`                 | `topics()`                            |

- `randomQuote`/`random_quote_filtered` nhận bộ lọc tùy chọn `{topic?, author?}`.
- `search` tìm không phân biệt hoa thường, không dấu (bỏ dấu tiếng Việt), trên cả `vi` và `en`.
- Kiểu `Quote`: `{ id, vi, en, author, topics }`.

## 5. Kiến trúc kỹ thuật

### npm (`packages/npm`)
- Mã nguồn TypeScript trong `src/`, biên dịch ra **ESM + CJS + .d.ts** (dùng `tsup`).
- `data/quotes.json` được copy vào package và `import` trực tiếp (đóng gói sẵn, không tải mạng).
- **Zero dependency** lúc chạy. Hỗ trợ Node ≥ 18 và bundler.
- Test bằng `vitest`.

### Rust (`packages/rust`)
- Nhúng `quotes.json` bằng `include_str!`, parse một lần qua `OnceLock` (lazy).
- Dependency: `serde`, `serde_json`. Random dùng RNG nhỏ tự cài (seed từ `SystemTime`) → không kéo `rand`.
- `struct Quote { id, vi, en, author, topics }` (derive `Serialize/Deserialize/Clone`).
- Test tích hợp trong `tests/`.

## 6. Bố cục repo (monorepo)

```
danh-ngon/
  data/                 # JSON chuẩn hoá (nguồn chung)
  scripts/build_dataset.py
  packages/npm/         # thư viện JS/TS
  packages/rust/        # crate Rust
  docs/superpowers/specs/
  .github/workflows/    # CI test + publish
  README.md             # tổng quan tiếng Việt
```

## 7. Xuất bản

- `git init`, commit, tạo repo GitHub (`gh`) nếu đăng nhập sẵn.
- npm: `npm publish` (cần `npm login`).
- crates.io: `cargo publish` (cần `cargo login`).
- Kèm hướng dẫn từng bước bằng tiếng Việt trong `PUBLISHING.md`; CI workflow tự publish khi tạo tag.

## 8. Phạm vi loại bỏ (YAGNI)

- Không tự suy luận chủ đề bằng AI/heuristic — đã có chủ đề từ tên sheet.
- Không API mạng, không database — dữ liệu tĩnh đóng gói sẵn.
- Không CLI ở v1 (có thể thêm sau).
