// Wildcard JSON module declaration – dùng khi resolveJsonModule: false.
// Cho phép TypeScript biết rằng "*.json" là module hợp lệ với kiểu `unknown`,
// tránh lỗi "Map maximum size exceeded" khi infer từ 30k-entry JSON array.
declare module "*.json" {
  const value: unknown;
  export default value;
}
