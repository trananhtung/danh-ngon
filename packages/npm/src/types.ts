/** Một câu danh ngôn. */
export interface Quote {
  id: number;
  vi: string;
  en: string;
  author: string;
  topics: string[];
}

/** Thông tin một chủ đề. */
export interface Topic {
  slug: string;
  label: string;
  count: number;
}

/** Thống kê tổng quan về bộ dữ liệu. */
export interface Meta {
  schemaVersion: number;
  totalQuotes: number;
  totalQuotesFull?: number;
  totalAuthors: number;
  totalTopics: number;
  withEnglish: number;
  withVietnamese?: number;
  source: string;
  fullDatasetPath?: string;
  fullDatasetFiles?: number;
  note?: string;
}

export interface RandomOptions {
  topic?: string;
  author?: string;
}

export interface SearchOptions {
  limit?: number;
  includeEnglish?: boolean;
}

export interface PageResult {
  quotes: Quote[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}
