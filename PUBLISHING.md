# Hướng dẫn xuất bản (Publishing)

Tài liệu này mô tả cách phát hành cả hai thư viện. Tất cả lệnh chạy từ thư mục gốc kho mã.

## 0. Build lại dữ liệu (khi cần)

```bash
python3 scripts/build_dataset.py
# Sau đó đồng bộ dữ liệu sang hai package:
cp data/quotes.min.json packages/npm/data/quotes.json
cp data/topics.json data/meta.json data/authors.json packages/npm/data/
cp data/quotes.min.json packages/rust/data/quotes.json
cp data/topics.json data/meta.json data/authors.json packages/rust/data/
```

## 1. GitHub

```bash
# Tạo repo và đẩy mã (cần `gh auth login` trước)
gh repo create danh-ngon --public --source=. --remote=origin --push
```

Hoặc thủ công:

```bash
git remote add origin https://github.com/<tài-khoản>/danh-ngon.git
git push -u origin main
```

## 2. npm

```bash
cd packages/npm
npm login              # nếu chưa đăng nhập
npm run build          # tạo dist/ (tự chạy khi publish nhờ prepublishOnly)
npm publish --access public
```

Kiểm tra trước khi publish:

```bash
npm pack --dry-run     # xem các tệp sẽ được đóng gói
```

## 3. crates.io

```bash
cd packages/rust
cargo login            # dán API token từ https://crates.io/me
cargo publish --dry-run   # kiểm tra
cargo publish
```

## 4. Phát hành phiên bản mới

1. Cập nhật `version` trong `packages/npm/package.json` và `packages/rust/Cargo.toml`.
2. Commit, tạo tag: `git tag vX.Y.Z && git push --tags`.
3. CI (`.github/workflows/publish.yml`) sẽ tự publish khi có tag `v*`,
   với điều kiện đã thiết lập secrets `NPM_TOKEN` và `CARGO_TOKEN` trong repo GitHub.

### Thiết lập secrets cho CI

Trong GitHub repo → Settings → Secrets and variables → Actions:

- `NPM_TOKEN`: token loại *Automation* từ npm.
- `CARGO_TOKEN`: API token từ crates.io.
