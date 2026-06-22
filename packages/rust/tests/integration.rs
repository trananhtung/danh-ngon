use danh_ngon::*;

#[test]
fn co_hang_nghin_cau() {
    assert!(count() > 9000);
    assert_eq!(all_quotes().len(), count());
}

#[test]
fn moi_cau_co_du_truong() {
    for q in all_quotes().iter().take(100) {
        assert!(!q.vi.is_empty() || !q.en.is_empty());
        assert!(!q.author.is_empty());
    }
}

#[test]
fn by_id_hoat_dong() {
    let first = &all_quotes()[10];
    assert_eq!(by_id(first.id), Some(first));
    assert_eq!(by_id(u32::MAX), None);
}

#[test]
fn random_quote_hop_le() {
    let q = random_quote();
    assert!(!q.vi.is_empty() || !q.en.is_empty());
}

#[test]
fn random_loc_theo_chu_de() {
    let q = random_quote_filtered(Some("tinh-yeu"), None).unwrap();
    assert!(q.topics.iter().any(|t| t == "tinh-yeu"));
}

#[test]
fn random_quotes_khong_trung() {
    let qs = random_quotes(5);
    assert_eq!(qs.len(), 5);
    let mut ids: Vec<u32> = qs.iter().map(|q| q.id).collect();
    ids.sort();
    ids.dedup();
    assert_eq!(ids.len(), 5);
}

#[test]
fn by_author_khong_phan_biet_dau() {
    let a = by_author("ho chi minh");
    let b = by_author("Hồ Chí Minh");
    assert!(!a.is_empty());
    assert_eq!(a.len(), b.len());
}

#[test]
fn by_topic_khop_slug() {
    let qs = by_topic("cuoc-song");
    assert!(qs.len() > 100);
    for q in qs {
        assert!(q.topics.iter().any(|t| t == "cuoc-song"));
    }
}

#[test]
fn search_khong_dau() {
    let voi_dau = search("hạnh phúc");
    let khong_dau = search("hanh phuc");
    assert!(!voi_dau.is_empty());
    assert_eq!(voi_dau.len(), khong_dau.len());
}

#[test]
fn topics_co_18_va_sap_giam_dan() {
    let t = topics();
    assert_eq!(t.len(), 18);
    for w in t.windows(2) {
        assert!(w[0].count >= w[1].count);
    }
}

#[test]
fn authors_ton_trong_limit() {
    assert_eq!(authors(5).len(), 5);
    assert!(authors(0).len() > 1000);
}

#[test]
fn normalize_dung() {
    assert_eq!(normalize("Hạnh Phúc"), "hanh phuc");
    assert_eq!(normalize("Đường ĐỜI"), "duong doi");
}
