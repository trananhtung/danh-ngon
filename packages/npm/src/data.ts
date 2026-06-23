// File trung gian: cast sang đúng type thay vì để TypeScript infer từ JSON.
// "as unknown as T" ngăn TypeScript tạo union type khổng lồ từ 30k entries
// (tránh lỗi "Map maximum size exceeded" khi DTS build).

import type { Quote, Meta } from "./types.js";
import quotesRaw from "../data/quotes.json";
import topicsRaw from "../data/topics.json";
import metaRaw from "../data/meta.json";

export const QUOTES: Quote[] = quotesRaw as unknown as Quote[];

export const TOPICS_RAW: Record<string, { label: string; count: number }> =
  topicsRaw as unknown as Record<string, { label: string; count: number }>;

export const META: Meta = metaRaw as unknown as Meta;
