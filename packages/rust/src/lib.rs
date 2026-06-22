//! # danh-ngon
//!
//! Kho **danh ngôn song ngữ Việt–Anh** với hơn 9.000 câu, đóng gói sẵn ngay trong
//! crate — không cần kết nối mạng, không cần tệp ngoài.
//!
//! Dữ liệu được nhúng bằng [`include_str!`] và phân tích một lần (lazy) khi dùng lần đầu.
//!
//! ## Ví dụ
//!
//! ```
//! use danh_ngon::{random_quote, by_topic, search};
//!
//! // Một câu ngẫu nhiên
//! let q = random_quote();
//! println!("\"{}\" — {}", q.vi, q.author);
//!
//! // Lọc theo chủ đề
//! let tinh_yeu = by_topic("tinh-yeu");
//! assert!(!tinh_yeu.is_empty());
//!
//! // Tìm kiếm không dấu
//! let kq = search("hanh phuc");
//! assert!(!kq.is_empty());
//! ```

use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

/// Một câu danh ngôn.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Quote {
    /// Mã định danh duy nhất, ổn định.
    pub id: u32,
    /// Nội dung tiếng Việt.
    pub vi: String,
    /// Nội dung tiếng Anh (chuỗi rỗng nếu không có bản dịch).
    pub en: String,
    /// Tên tác giả ("Khuyết danh" nếu không rõ).
    pub author: String,
    /// Danh sách slug chủ đề, ví dụ `["cuoc-song", "thanh-cong"]`.
    pub topics: Vec<String>,
}

/// Thông tin một chủ đề.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Topic {
    /// Slug dùng để lọc, ví dụ `"cuoc-song"`.
    pub slug: String,
    /// Nhãn tiếng Việt, ví dụ `"Cuộc sống"`.
    pub label: String,
    /// Số câu thuộc chủ đề.
    pub count: u32,
}

#[derive(Deserialize)]
struct TopicInfo {
    label: String,
    count: u32,
}

const QUOTES_JSON: &str = include_str!("../data/quotes.json");
const TOPICS_JSON: &str = include_str!("../data/topics.json");

static QUOTES: OnceLock<Vec<Quote>> = OnceLock::new();
static TOPICS: OnceLock<Vec<Topic>> = OnceLock::new();

fn quotes() -> &'static Vec<Quote> {
    QUOTES.get_or_init(|| serde_json::from_str(QUOTES_JSON).expect("quotes.json hợp lệ"))
}

fn topics_map() -> &'static Vec<Topic> {
    TOPICS.get_or_init(|| {
        let raw: std::collections::BTreeMap<String, TopicInfo> =
            serde_json::from_str(TOPICS_JSON).expect("topics.json hợp lệ");
        let mut v: Vec<Topic> = raw
            .into_iter()
            .map(|(slug, info)| Topic {
                slug,
                label: info.label,
                count: info.count,
            })
            .collect();
        v.sort_by_key(|t| std::cmp::Reverse(t.count));
        v
    })
}

/// Trả về toàn bộ danh ngôn (tham chiếu, không tốn bộ nhớ sao chép).
pub fn all_quotes() -> &'static [Quote] {
    quotes().as_slice()
}

/// Tổng số câu danh ngôn.
pub fn count() -> usize {
    quotes().len()
}

/// Lấy một câu theo `id`.
pub fn by_id(id: u32) -> Option<&'static Quote> {
    quotes().iter().find(|q| q.id == id)
}

/// Sinh số ngẫu nhiên đơn giản (xorshift64) seed từ thời gian + bộ đếm,
/// đủ dùng để chọn câu ngẫu nhiên mà không cần phụ thuộc ngoài.
fn next_rand() -> u64 {
    use std::sync::atomic::{AtomicU64, Ordering};
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(0x9E3779B97F4A7C15);
    let c = COUNTER.fetch_add(1, Ordering::Relaxed);
    let mut x = nanos ^ (c.wrapping_mul(0x9E3779B97F4A7C15)).wrapping_add(0xD1B54A32D192ED03);
    if x == 0 {
        x = 0x9E3779B97F4A7C15;
    }
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    x
}

fn pick(pool: &[&'static Quote]) -> Option<&'static Quote> {
    if pool.is_empty() {
        return None;
    }
    let idx = (next_rand() % pool.len() as u64) as usize;
    Some(pool[idx])
}

/// Lấy một câu danh ngôn ngẫu nhiên.
///
/// # Panics
/// Không panic; kho dữ liệu luôn có sẵn câu.
pub fn random_quote() -> &'static Quote {
    let all = quotes();
    let idx = (next_rand() % all.len() as u64) as usize;
    &all[idx]
}

/// Lấy một câu ngẫu nhiên có lọc theo chủ đề và/hoặc tác giả.
///
/// Trả về `None` nếu không có câu nào khớp bộ lọc.
pub fn random_quote_filtered(topic: Option<&str>, author: Option<&str>) -> Option<&'static Quote> {
    let author_n = author.map(normalize);
    let pool: Vec<&'static Quote> = quotes()
        .iter()
        .filter(|q| match topic {
            Some(t) => q.topics.iter().any(|s| s == t),
            None => true,
        })
        .filter(|q| match &author_n {
            Some(a) => normalize(&q.author).contains(a.as_str()),
            None => true,
        })
        .collect();
    pick(&pool)
}

/// Lấy `n` câu ngẫu nhiên khác nhau (không trùng).
pub fn random_quotes(n: usize) -> Vec<&'static Quote> {
    let all = quotes();
    let len = all.len();
    let take = n.min(len);
    let mut chosen = Vec::with_capacity(take);
    let mut used = vec![false; len];
    let mut guard = 0u64;
    while chosen.len() < take {
        let idx = (next_rand() % len as u64) as usize;
        if !used[idx] {
            used[idx] = true;
            chosen.push(&all[idx]);
        }
        guard += 1;
        if guard > (len as u64) * 20 {
            // Dự phòng: quét tuần tự nếu xui xẻo va chạm nhiều.
            for (i, u) in used.iter().enumerate() {
                if !u && chosen.len() < take {
                    chosen.push(&all[i]);
                }
            }
            break;
        }
    }
    chosen
}

/// Lọc danh ngôn theo tác giả (so khớp một phần, không phân biệt dấu/hoa thường).
pub fn by_author(author: &str) -> Vec<&'static Quote> {
    let a = normalize(author);
    if a.is_empty() {
        return Vec::new();
    }
    quotes()
        .iter()
        .filter(|q| normalize(&q.author).contains(a.as_str()))
        .collect()
}

/// Lọc danh ngôn theo slug chủ đề (so khớp chính xác slug).
pub fn by_topic(topic: &str) -> Vec<&'static Quote> {
    quotes()
        .iter()
        .filter(|q| q.topics.iter().any(|s| s == topic))
        .collect()
}

/// Tìm kiếm theo từ khoá trên nội dung Việt/Anh và tác giả.
/// Không phân biệt dấu và hoa thường.
pub fn search(keyword: &str) -> Vec<&'static Quote> {
    let kw = normalize(keyword);
    if kw.is_empty() {
        return Vec::new();
    }
    quotes()
        .iter()
        .filter(|q| {
            normalize(&q.vi).contains(kw.as_str())
                || normalize(&q.en).contains(kw.as_str())
                || normalize(&q.author).contains(kw.as_str())
        })
        .collect()
}

/// Danh sách chủ đề kèm nhãn tiếng Việt và số lượng (giảm dần theo số lượng).
pub fn topics() -> &'static [Topic] {
    topics_map().as_slice()
}

/// Danh sách tác giả kèm số lượng câu, sắp giảm dần.
///
/// `limit = 0` nghĩa là lấy tất cả.
pub fn authors(limit: usize) -> Vec<(String, usize)> {
    use std::collections::HashMap;
    let mut counts: HashMap<&str, usize> = HashMap::new();
    for q in quotes() {
        *counts.entry(q.author.as_str()).or_insert(0) += 1;
    }
    let mut v: Vec<(String, usize)> = counts.into_iter().map(|(k, n)| (k.to_string(), n)).collect();
    v.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    if limit > 0 && limit < v.len() {
        v.truncate(limit);
    }
    v
}

/// Bỏ dấu tiếng Việt + chuyển chữ thường, phục vụ tìm kiếm không phân biệt dấu.
pub fn normalize(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for ch in text.chars() {
        for low in ch.to_lowercase() {
            out.push(strip_vn(low));
        }
    }
    out.trim().to_string()
}

/// Ánh xạ một ký tự tiếng Việt (đã ở dạng thường) về ký tự ASCII cơ sở.
fn strip_vn(c: char) -> char {
    match c {
        'à' | 'á' | 'ả' | 'ã' | 'ạ' | 'ă' | 'ằ' | 'ắ' | 'ẳ' | 'ẵ' | 'ặ' | 'â' | 'ầ' | 'ấ'
        | 'ẩ' | 'ẫ' | 'ậ' => 'a',
        'è' | 'é' | 'ẻ' | 'ẽ' | 'ẹ' | 'ê' | 'ề' | 'ế' | 'ể' | 'ễ' | 'ệ' => 'e',
        'ì' | 'í' | 'ỉ' | 'ĩ' | 'ị' => 'i',
        'ò' | 'ó' | 'ỏ' | 'õ' | 'ọ' | 'ô' | 'ồ' | 'ố' | 'ổ' | 'ỗ' | 'ộ' | 'ơ' | 'ờ' | 'ớ'
        | 'ở' | 'ỡ' | 'ợ' => 'o',
        'ù' | 'ú' | 'ủ' | 'ũ' | 'ụ' | 'ư' | 'ừ' | 'ứ' | 'ử' | 'ữ' | 'ự' => 'u',
        'ỳ' | 'ý' | 'ỷ' | 'ỹ' | 'ỵ' => 'y',
        'đ' => 'd',
        other => other,
    }
}
