# danh-ngon

> Kho **danh ngôn song ngữ Việt–Anh** với hơn **31.000 câu song ngữ**, đóng gói sẵn trong thư viện — không cần kết nối mạng, không cần API key.

[![npm](https://img.shields.io/npm/v/danh-ngon.svg)](https://www.npmjs.com/package/danh-ngon)

Phù hợp cho: ứng dụng "danh ngôn mỗi ngày", widget, bot Telegram/Discord, màn hình chờ, app học tiếng Anh, nội dung mạng xã hội, v.v.

## Tính năng

- 📚 **31.000+ danh ngôn** kèm bản dịch tiếng Anh và tên tác giả.
- 🏷️ **18 chủ đề**: cuộc sống, tình yêu, thành công, giáo dục, thời gian, sự nghiệp, gia đình, tình bạn, trí tuệ…
- 🔍 **Tìm kiếm không dấu** (gõ `hanh phuc` vẫn ra `hạnh phúc`).
- 🎲 Lấy câu **ngẫu nhiên**, có thể lọc theo chủ đề/tác giả.
- ⚡ **Zero dependency**, dữ liệu nhúng sẵn, hỗ trợ cả ESM và CommonJS, có sẵn type cho TypeScript.

## Cài đặt

```bash
npm install danh-ngon
# hoặc: yarn add danh-ngon / pnpm add danh-ngon
```

## Bắt đầu nhanh

```ts
import { randomQuote, quotesByTopic, search } from "danh-ngon";

// Một câu ngẫu nhiên
const q = randomQuote();
console.log(`"${q.vi}" — ${q.author}`);

// Câu ngẫu nhiên thuộc chủ đề Tình yêu
console.log(randomQuote({ topic: "tinh-yeu" })?.vi);

// Tìm theo từ khoá (không phân biệt dấu)
const ket_qua = search("thanh cong", { limit: 5 });
console.log(`Tìm thấy ${ket_qua.length} câu.`);
```

CommonJS cũng dùng được:

```js
const { randomQuote } = require("danh-ngon");
console.log(randomQuote().vi);
```

## Kiểu dữ liệu

```ts
interface Quote {
  id: number;        // mã định danh ổn định
  vi: string;        // nội dung tiếng Việt
  en: string;        // bản tiếng Anh ("" nếu không có)
  author: string;    // tác giả ("Khuyết danh" nếu không rõ)
  topics: string[];  // các slug chủ đề
}
```

## API

| Hàm | Mô tả |
|-----|-------|
| `getAllQuotes(): Quote[]` | Toàn bộ danh ngôn. |
| `count(): number` | Tổng số câu. |
| `getMeta(): Meta` | Thống kê tổng quan. |
| `getQuoteById(id): Quote \| undefined` | Lấy câu theo id. |
| `randomQuote(opts?): Quote \| undefined` | Một câu ngẫu nhiên (lọc `{topic, author}`). |
| `randomQuotes(n, opts?): Quote[]` | `n` câu ngẫu nhiên, không trùng. |
| `quotesByAuthor(name): Quote[]` | Lọc theo tác giả (không phân biệt dấu/hoa thường). |
| `quotesByTopic(slug): Quote[]` | Lọc theo slug chủ đề. |
| `search(keyword, opts?): Quote[]` | Tìm trên VI/EN/tác giả (`{limit, includeEnglish}`). |
| `listTopics(): Topic[]` | Danh sách chủ đề kèm số lượng. |
| `listAuthors(limit?): {author, count}[]` | Tác giả kèm số lượng, giảm dần. |

### Danh sách chủ đề (slug)

`cuoc-song`, `tinh-yeu`, `nhung-manh-ngon-tinh`, `su-nghiep`, `tieng-anh`,
`tinh-ban`, `song-chet`, `thoi-gian`, `trai-tim`, `giao-duc`, `yeu-nuoc`,
`tri-tue`, `tam-hon`, `van-minh-khoa-hoc`, `gia-dinh`, `thanh-cong`,
`trich-dan-hay`, `thay-doi`.

Gọi `listTopics()` để lấy nhãn tiếng Việt và số lượng chính xác.

## Ví dụ: "Danh ngôn mỗi ngày"

```ts
import { randomQuote } from "danh-ngon";

function danhNgonHomNay() {
  const q = randomQuote({ topic: "cuoc-song" })!;
  return `🌅 ${q.vi}\n   — ${q.author}\n   (${q.en})`;
}

console.log(danhNgonHomNay());
```

## Nguồn dữ liệu & giấy phép

Dữ liệu được tổng hợp và chuẩn hoá từ kho danh ngôn cộng đồng. Mã nguồn thư viện phát hành theo giấy phép **MIT**.

Đóng góp, báo lỗi dữ liệu: xem repository trên GitHub.
