// File trung gian: ép kiểu dữ liệu JSON thay vì để TypeScript tự infer.
// Tránh lỗi "Map maximum size exceeded" khi DTS build gặp 30k+ entries.

import type { Quote, Meta } from "./types.js";

// eslint-disable-next-line @typescript-eslint/no-require-imports
export const QUOTES: Quote[] = require("../data/quotes.json") as Quote[];

// eslint-disable-next-line @typescript-eslint/no-require-imports
export const TOPICS_RAW: Record<string, { label: string; count: number }> =
  require("../data/topics.json") as Record<string, { label: string; count: number }>;

// eslint-disable-next-line @typescript-eslint/no-require-imports
export const META: Meta = require("../data/meta.json") as Meta;
