/**
 * danh-ngon — Kho danh ngôn song ngữ Việt–Anh đóng gói sẵn.
 *
 * Toàn bộ dữ liệu được nhúng trong thư viện, không cần kết nối mạng.
 * Xem README.md để biết hướng dẫn chi tiết bằng tiếng Việt.
 */

export type {
  Quote,
  Topic,
  Meta,
  RandomOptions,
  SearchOptions,
  PageResult,
} from "./types.js";

import type { Quote, Meta, RandomOptions, SearchOptions, PageResult } from "./types.js";
import { QUOTES, TOPICS_RAW, META } from "./data.js";

// Lazy indexes – built on first use to keep initial load fast.
let _topicIndex: Map<string, Quote[]> | null = null;
let _authorIndex: Map<string, Quote[]> | null = null;

function getTopicIndex(): Map<string, Quote[]> {
  if (!_topicIndex) {
    _topicIndex = new Map();
    for (const q of QUOTES) {
      for (const t of q.topics) {
        const arr = _topicIndex.get(t) ?? [];
        arr.push(q);
        _topicIndex.set(t, arr);
      }
    }
  }
  return _topicIndex;
}

function getAuthorIndex(): Map<string, Quote[]> {
  if (!_authorIndex) {
    _authorIndex = new Map();
    for (const q of QUOTES) {
      const key = normalize(q.author);
      const arr = _authorIndex.get(key) ?? [];
      arr.push(q);
      _authorIndex.set(key, arr);
    }
  }
  return _authorIndex;
}

/** Bỏ dấu tiếng Việt + chuyển thường, phục vụ tìm kiếm không phân biệt dấu. */
function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

/** Lấy toàn bộ danh ngôn. */
export function getAllQuotes(): Quote[] {
  return QUOTES.slice();
}

/** Tổng số câu danh ngôn hiện có trong thư viện (bilingual EN+VI). */
export function count(): number {
  return QUOTES.length;
}

/** Lấy thông tin thống kê tổng quan của bộ dữ liệu. */
export function getMeta(): Meta {
  return { ...META };
}

/**
 * Lấy một câu theo id.
 *
 * @param id Mã định danh.
 */
export function getQuoteById(id: number): Quote | undefined {
  return QUOTES.find((q) => q.id === id);
}

/**
 * Lấy một câu danh ngôn ngẫu nhiên, có thể lọc theo chủ đề/tác giả.
 * Sử dụng lazy index để tối ưu hiệu năng.
 */
export function randomQuote(opts: RandomOptions = {}): Quote | undefined {
  let pool: readonly Quote[];
  if (opts.topic) {
    pool = getTopicIndex().get(opts.topic) ?? [];
  } else if (opts.author) {
    pool = quotesByAuthor(opts.author);
  } else {
    pool = QUOTES;
  }
  if (pool.length === 0) return undefined;
  return pool[Math.floor(Math.random() * pool.length)];
}

/**
 * Lấy nhiều câu ngẫu nhiên khác nhau (không lặp lại).
 *
 * @param n Số lượng câu muốn lấy.
 */
export function randomQuotes(n: number, opts: RandomOptions = {}): Quote[] {
  let pool: Quote[];
  if (opts.topic) {
    pool = getTopicIndex().get(opts.topic)?.slice() ?? [];
  } else if (opts.author) {
    pool = quotesByAuthor(opts.author);
  } else {
    pool = QUOTES.slice();
  }
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, Math.max(0, n));
}

/**
 * Lọc danh ngôn theo tác giả (so khớp một phần, không phân biệt dấu/hoa thường).
 * Tìm khớp chính xác O(1) trước, rồi partial match nếu không có.
 */
export function quotesByAuthor(author: string): Quote[] {
  const a = normalize(author);
  if (!a) return [];
  const idx = getAuthorIndex();
  const exact = idx.get(a);
  if (exact) return exact.slice();
  const results: Quote[] = [];
  for (const [key, quotes] of idx) {
    if (key.includes(a)) results.push(...quotes);
  }
  return results;
}

/**
 * Lọc danh ngôn theo slug chủ đề – O(1) nhờ lazy index.
 *
 * @param topic Slug chủ đề, ví dụ "tinh-yeu". Xem {@link listTopics}.
 */
export function quotesByTopic(topic: string): Quote[] {
  return getTopicIndex().get(topic)?.slice() ?? [];
}

/**
 * Lấy danh ngôn theo trang (pagination).
 *
 * @param page Số trang (bắt đầu từ 1).
 * @param pageSize Số câu mỗi trang (mặc định: 20).
 * @param opts Lọc theo chủ đề/tác giả (tùy chọn).
 */
export function getPage(page: number, pageSize = 20, opts: RandomOptions = {}): PageResult {
  let pool: Quote[];
  if (opts.topic) {
    pool = getTopicIndex().get(opts.topic) ?? [];
  } else if (opts.author) {
    pool = quotesByAuthor(opts.author);
  } else {
    pool = QUOTES;
  }
  const total = pool.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    quotes: pool.slice(start, start + pageSize),
    page: safePage,
    pageSize,
    total,
    totalPages,
  };
}

/**
 * Tìm kiếm theo từ khoá trên nội dung Việt/Anh và tên tác giả.
 * Không phân biệt dấu và hoa thường.
 */
export function search(keyword: string, opts: SearchOptions = {}): Quote[] {
  const kw = normalize(keyword);
  if (!kw) return [];
  const includeEn = opts.includeEnglish !== false;
  const results = QUOTES.filter((q) => {
    if (normalize(q.vi).includes(kw)) return true;
    if (normalize(q.author).includes(kw)) return true;
    if (includeEn && normalize(q.en).includes(kw)) return true;
    return false;
  });
  return opts.limit != null ? results.slice(0, opts.limit) : results;
}

/**
 * Liệt kê toàn bộ chủ đề kèm nhãn tiếng Việt và số lượng câu.
 */
export function listTopics() {
  return Object.entries(TOPICS_RAW)
    .map(([slug, v]) => ({ slug, label: v.label, count: v.count }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Liệt kê các tác giả kèm số lượng câu, sắp theo số lượng giảm dần.
 *
 * @param limit Giới hạn số tác giả trả về (mặc định: tất cả).
 */
export function listAuthors(limit?: number): { author: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const q of QUOTES) {
    counts.set(q.author, (counts.get(q.author) ?? 0) + 1);
  }
  const arr = Array.from(counts, ([author, c]) => ({ author, count: c })).sort(
    (a, b) => b.count - a.count || a.author.localeCompare(b.author, "vi"),
  );
  return limit != null ? arr.slice(0, limit) : arr;
}
