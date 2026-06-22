import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  outExtension({ format }) {
    return { js: format === "cjs" ? ".cjs" : ".js" };
  },
  dts: true,
  clean: true,
  minify: false,
  // Nhúng thẳng các file JSON vào bundle để package tự chứa dữ liệu.
  loader: { ".json": "json" },
  treeshake: true,
});
