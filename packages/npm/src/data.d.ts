// Khai báo type thủ công để tránh TypeScript inferring toàn bộ 30k-entry JSON
// (dẫn đến lỗi "Map maximum size exceeded" khi build DTS)

declare module "../data/quotes.json" {
  const value: Array<{
    id: number;
    vi: string;
    en: string;
    author: string;
    topics: string[];
  }>;
  export default value;
}

declare module "../data/topics.json" {
  const value: Record<string, { label: string; count: number }>;
  export default value;
}

declare module "../data/meta.json" {
  const value: {
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
  };
  export default value;
}
