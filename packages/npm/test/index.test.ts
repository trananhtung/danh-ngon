import { describe, it, expect } from "vitest";
import {
  getAllQuotes,
  count,
  getMeta,
  getQuoteById,
  randomQuote,
  randomQuotes,
  quotesByAuthor,
  quotesByTopic,
  search,
  listTopics,
  listAuthors,
} from "../src/index.js";

describe("danh-ngon", () => {
  it("có hàng nghìn câu danh ngôn", () => {
    expect(count()).toBeGreaterThan(9000);
    expect(getAllQuotes().length).toBe(count());
  });

  it("meta khớp số lượng thực tế", () => {
    const m = getMeta();
    expect(m.totalQuotes).toBe(count());
    expect(m.totalTopics).toBe(18);
  });

  it("mỗi câu có đủ trường", () => {
    for (const q of getAllQuotes().slice(0, 100)) {
      expect(typeof q.id).toBe("number");
      expect(typeof q.vi).toBe("string");
      expect(typeof q.en).toBe("string");
      expect(typeof q.author).toBe("string");
      expect(Array.isArray(q.topics)).toBe(true);
    }
  });

  it("getQuoteById trả đúng câu", () => {
    const all = getAllQuotes();
    const target = all[42];
    expect(getQuoteById(target.id)).toEqual(target);
    expect(getQuoteById(-1)).toBeUndefined();
  });

  it("randomQuote luôn trả về câu hợp lệ", () => {
    const q = randomQuote();
    expect(q).toBeDefined();
    expect(q!.vi.length).toBeGreaterThan(0);
  });

  it("randomQuote lọc theo chủ đề", () => {
    const q = randomQuote({ topic: "tinh-yeu" });
    expect(q).toBeDefined();
    expect(q!.topics).toContain("tinh-yeu");
  });

  it("randomQuotes trả về số lượng yêu cầu, không trùng", () => {
    const qs = randomQuotes(5);
    expect(qs.length).toBe(5);
    const ids = new Set(qs.map((q) => q.id));
    expect(ids.size).toBe(5);
  });

  it("quotesByAuthor không phân biệt dấu/hoa thường", () => {
    const a = quotesByAuthor("ho chi minh");
    const b = quotesByAuthor("Hồ Chí Minh");
    expect(a.length).toBeGreaterThan(0);
    expect(a.length).toBe(b.length);
  });

  it("quotesByTopic khớp slug", () => {
    const qs = quotesByTopic("cuoc-song");
    expect(qs.length).toBeGreaterThan(100);
    for (const q of qs) expect(q.topics).toContain("cuoc-song");
  });

  it("search không dấu vẫn ra kết quả", () => {
    const withTone = search("hạnh phúc");
    const without = search("hanh phuc");
    expect(withTone.length).toBeGreaterThan(0);
    expect(without.length).toBe(withTone.length);
  });

  it("search tôn trọng limit", () => {
    const r = search("cuộc sống", { limit: 3 });
    expect(r.length).toBeLessThanOrEqual(3);
  });

  it("listTopics sắp giảm dần theo count", () => {
    const t = listTopics();
    expect(t.length).toBe(18);
    for (let i = 1; i < t.length; i++) {
      expect(t[i - 1].count).toBeGreaterThanOrEqual(t[i].count);
    }
  });

  it("listAuthors tôn trọng limit", () => {
    expect(listAuthors(5).length).toBe(5);
    expect(listAuthors().length).toBeGreaterThan(1000);
  });
});
