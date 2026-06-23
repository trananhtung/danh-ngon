#!/usr/bin/env python3
"""
Crawl quotes từ nhiều nguồn + dịch song ngữ EN-VI.

Nguồn chính:
  1. AZQuotes.com       (~500k quotes - authors a-z)
  2. Wikiquote EN API   (~300k quotes)
  3. Wikiquote VI API   (~20k quotes)
  4. GitHub open datasets (~15k quotes)
  5. wisdomquotes.com   (~5k quotes)
  6. quotationspage.com (~10k quotes)

Usage:
  python3 scripts/crawl_quotes.py [--source SOURCE] [--letters A-Z] [--translate] [--merge]
"""

import argparse
import json
import re
import sys
import time
import unicodedata
import threading
import concurrent.futures
import hashlib
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCRATCHPAD = Path("/tmp/danh-ngon-crawl")
SCRATCHPAD.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

_rate_locks = {}
_rate_times = {}
_global_lock = threading.Lock()

def rate_limited_get(url, delay=0.5, **kwargs):
    domain = "/".join(url.split("/")[:3])
    with _global_lock:
        if domain not in _rate_locks:
            _rate_locks[domain] = threading.Lock()
    lock = _rate_locks[domain]
    with lock:
        last = _rate_times.get(domain, 0)
        wait = delay - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        _rate_times[domain] = time.time()
    try:
        r = SESSION.get(url, timeout=20, **kwargs)
        if r.status_code == 429:
            retry_after = float(r.headers.get("Retry-After", 5))
            time.sleep(retry_after)
            r = SESSION.get(url, timeout=20, **kwargs)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        print(f"  [HTTP] {url} failed: {e}", file=sys.stderr)
        return None

def clean(t):
    if not t:
        return ""
    t = t.strip()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[​‌‍‎‏﻿]', '', t)
    return t

# ────────────────────────────────────────────────────────────────────────────
# SOURCE 1: AZQuotes.com
# ────────────────────────────────────────────────────────────────────────────

def azquotes_get_author_links(letter):
    """Lấy tất cả author links cho 1 chữ cái."""
    url = f"https://www.azquotes.com/authors/{letter.lower()}"
    cache = SCRATCHPAD / f"azq_authors_{letter}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    links = []
    page = 1
    while True:
        page_url = url if page == 1 else f"{url}/{page}"
        r = rate_limited_get(page_url, delay=0.5)
        if not r:
            break
        soup = BeautifulSoup(r.text, 'html.parser')
        new_links = [
            {"name": a.text.strip(), "href": a.get("href", "")}
            for a in soup.select("a[href*='/author/']")
            if a.get("href", "").startswith("/author/")
        ]
        if not new_links:
            break
        links.extend(new_links)
        # Kiểm tra next page
        next_el = soup.select_one("a[rel='next'], .next a")
        if not next_el:
            break
        page += 1
        if page > 10:
            break

    links = list({l["href"]: l for l in links}.values())
    cache.write_text(json.dumps(links, ensure_ascii=False))
    return links

def azquotes_get_author_quotes(author_href, author_name):
    """Lấy tất cả quotes của 1 author trên AZQuotes."""
    base = "https://www.azquotes.com"
    all_quotes = []
    page = 1
    while True:
        url = f"{base}{author_href}" if page == 1 else f"{base}{author_href}/{page}"
        r = rate_limited_get(url, delay=0.4)
        if not r:
            break

        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.select(".wrap-block")
        if not items:
            break

        found = 0
        for item in items:
            q_el = item.select_one(".quote-body, a.title")
            if not q_el:
                continue
            text = clean(q_el.text)
            # Bỏ quotes quá ngắn hoặc quá dài
            if len(text) < 20 or len(text) > 2000:
                continue
            # Lấy author từ page nếu có
            auth_el = item.select_one(".author a")
            author = clean(auth_el.text) if auth_el else author_name
            all_quotes.append({
                "en": text,
                "author": author or author_name,
                "topics": [],
                "_source": "azquotes",
            })
            found += 1

        if found == 0:
            break
        # Kiểm tra có trang kế tiếp không
        next_el = soup.select_one("a.next, a[rel='next']")
        if not next_el:
            break
        page += 1
        if page > 20:  # max 20 pages per author
            break

    return all_quotes

def crawl_azquotes(letters="abcdefghijklmnopqrstuvwxyz", max_authors=None):
    """Crawl AZQuotes cho một nhóm chữ cái."""
    all_quotes = []
    cache_file = SCRATCHPAD / f"azquotes_{letters.replace('/', '_')}.json"

    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        print(f"[AZQuotes-{letters}] Loaded {len(data)} from cache")
        return data

    # Thu thập tất cả author links
    all_authors = []
    for letter in letters:
        links = azquotes_get_author_links(letter)
        all_authors.extend(links)
        print(f"  [AZQuotes] {letter.upper()}: {len(links)} authors")

    print(f"[AZQuotes-{letters}] Total authors: {len(all_authors)}")

    if max_authors:
        all_authors = all_authors[:max_authors]

    # Crawl từng author
    for i, author in enumerate(all_authors):
        href = author.get("href", "")
        name = author.get("name", "Unknown")
        if not href:
            continue

        quotes = azquotes_get_author_quotes(href, name)
        all_quotes.extend(quotes)

        if (i + 1) % 50 == 0:
            # Checkpoint
            cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
            print(f"  [AZQuotes-{letters}] {i+1}/{len(all_authors)} authors → {len(all_quotes)} quotes")

    cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
    print(f"[AZQuotes-{letters}] DONE: {len(all_quotes)} quotes")
    return all_quotes

# ────────────────────────────────────────────────────────────────────────────
# SOURCE 2: Wikiquote EN
# ────────────────────────────────────────────────────────────────────────────

def wikiquote_get_pages(lang="en", apcontinue=None):
    """Lấy danh sách tất cả pages từ Wikiquote theo batches."""
    base = f"https://{lang}.wikiquote.org/w/api.php"
    cache_file = SCRATCHPAD / f"wq_{lang}_pages.json"

    if cache_file.exists() and not apcontinue:
        pages = json.loads(cache_file.read_text())
        print(f"[Wikiquote-{lang}] Loaded {len(pages)} page list from cache")
        return pages

    pages = []
    params = {
        "action": "query",
        "list": "allpages",
        "apnamespace": 0,
        "aplimit": 500,
        "format": "json",
    }
    if apcontinue:
        params["apcontinue"] = apcontinue

    printed = 0
    while True:
        r = rate_limited_get(base, delay=0.2, params=params,
                             headers={"User-Agent": "QuoteBot/1.0 (educational)"})
        if not r:
            break
        data = r.json()
        batch = data.get("query", {}).get("allpages", [])
        pages.extend(batch)
        printed += len(batch)
        if printed >= 2000:
            print(f"  [Wikiquote-{lang}] Pages: {len(pages)}")
            printed = 0
        cont = data.get("continue", {})
        if not cont:
            break
        params["apcontinue"] = cont.get("apcontinue", "")
        if not params["apcontinue"]:
            break

    cache_file.write_text(json.dumps(pages, ensure_ascii=False))
    print(f"[Wikiquote-{lang}] Got {len(pages)} total pages")
    return pages

SKIP_PATS = [
    '(film)', '(TV', '(album)', '(book)', '(novel)', '(song)', '(game)',
    '(show)', '(series)', '(phim)', '(bài hát)', '(album)',
    'Wikipedia:', 'Wikiquote:', 'Template:', 'Category:', 'File:',
    'Help:', 'Talk:', 'Thể loại:', 'Tập tin:', 'Giúp đỡ:',
    'MediaWiki:', 'User:', 'Portal:',
]

def is_person_page(title):
    return not any(pat in title for pat in SKIP_PATS)

def wikiquote_extract_from_wikitext(wikitext, author, lang="en"):
    """Trích xuất quotes từ wikitext."""
    quotes = []
    field = "en" if lang == "en" else "vi"

    for line in wikitext.split('\n'):
        line = line.strip()
        if not (line.startswith('* ') or line.startswith('*"') or line.startswith("*'")):
            continue
        text = line.lstrip('*').strip()
        # Bỏ wiki markup
        text = re.sub(r"'{2,3}", '', text)
        text = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', text)
        text = re.sub(r'\{\{[^}]*\}\}', '', text)
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'❝|❞|„|"', '"', text)
        text = clean(text)

        if len(text) < 15:
            continue
        if text.startswith('(') or '|' in text[:5]:
            continue
        if text.startswith('See also') or text.startswith('Xem thêm'):
            continue
        # Lọc non-English cho EN wikiquote (cho phép một ít quotes nước ngoài)
        if lang == "en" and len(text) > 20:
            # Bỏ lines chỉ toàn chữ không phải Latin (ngôn ngữ khác)
            latin_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
            if latin_chars < len(text) * 0.3 and len(text) > 30:
                continue

        quotes.append({field: text, "author": author, "topics": [], "_source": f"wikiquote_{lang}"})

    return quotes

def crawl_wikiquote_lang(lang="en", title_from=None, title_to=None):
    """Crawl Wikiquote cho một ngôn ngữ, giới hạn bởi title range."""
    cache_file = SCRATCHPAD / f"wq_{lang}_quotes_{title_from or 'all'}_{title_to or 'z'}.json".replace('/', '_')

    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        print(f"[Wikiquote-{lang}] Loaded {len(data)} quotes from cache ({title_from}-{title_to})")
        return data

    all_pages = wikiquote_get_pages(lang)
    pages = [p for p in all_pages if is_person_page(p['title'])]

    # Filter by title range
    if title_from:
        pages = [p for p in pages if p['title'].upper() >= title_from.upper()]
    if title_to:
        pages = [p for p in pages if p['title'].upper() < title_to.upper()]

    print(f"[Wikiquote-{lang}] Processing {len(pages)} pages ({title_from}-{title_to})")

    base = f"https://{lang}.wikiquote.org/w/api.php"
    all_quotes = []
    done_titles = set()

    for idx, page in enumerate(pages):
        title = page['title']
        if title in done_titles:
            continue

        params = {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
        }
        r = rate_limited_get(base, delay=0.25, params=params,
                             headers={"User-Agent": "QuoteBot/1.0 (educational)"})
        if not r:
            continue

        data = r.json()
        if "error" in data:
            continue

        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        quotes = wikiquote_extract_from_wikitext(wikitext, title, lang)
        for q in quotes:
            q["_page"] = title
        all_quotes.extend(quotes)
        done_titles.add(title)

        if (idx + 1) % 200 == 0:
            cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
            print(f"  [Wikiquote-{lang}] {idx+1}/{len(pages)} → {len(all_quotes)} quotes")

    cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
    print(f"[Wikiquote-{lang}] DONE: {len(all_quotes)} quotes")
    return all_quotes

# ────────────────────────────────────────────────────────────────────────────
# SOURCE 3: GitHub open datasets
# ────────────────────────────────────────────────────────────────────────────

GITHUB_DATASETS = [
    {
        "name": "JamesFT",
        "url": "https://raw.githubusercontent.com/JamesFT/Database-Quotes-JSON/master/quotes.json",
        "encoding": "latin-1",
        "fields": {"en": ["quoteText"], "author": ["quoteAuthor"]},
    },
    {
        "name": "skolakoda",
        "url": "https://raw.githubusercontent.com/skolakoda/programming-quotes-api/master/backup/quotes.json",
        "encoding": "utf-8",
        "fields": {"en": ["en", "text", "body"], "author": ["author", "Author"]},
    },
    {
        "name": "dwyl",
        "url": "https://raw.githubusercontent.com/dwyl/quotes/main/quotes.json",
        "encoding": "utf-8",
        "fields": {"en": ["text", "quote", "body", "en"], "author": ["author", "Author"]},
    },
    {
        "name": "anbuchelva",
        "url": "https://raw.githubusercontent.com/anbuchelva/quotes/main/quotes.json",
        "encoding": "utf-8",
        "fields": {"en": ["quote", "text", "en"], "author": ["author", "Author"]},
    },
    {
        "name": "vikasverma77",
        "url": "https://raw.githubusercontent.com/vikasverma77/quotes/master/quotes.json",
        "encoding": "utf-8",
        "fields": {"en": ["quote", "text", "en"], "author": ["author", "Author"]},
    },
]

def crawl_github_datasets():
    """Download open-source quote datasets từ GitHub."""
    cache_file = SCRATCHPAD / "github_all.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        print(f"[GitHub] Loaded {len(data)} from cache")
        return data

    all_quotes = []
    for ds in GITHUB_DATASETS:
        r = rate_limited_get(ds["url"], delay=0)
        if not r:
            print(f"  [GitHub-{ds['name']}] FAILED")
            continue
        try:
            raw = r.content.decode(ds.get("encoding", "utf-8"), errors="replace")
            data = json.loads(raw)
        except Exception as e:
            print(f"  [GitHub-{ds['name']}] Parse error: {e}")
            continue

        items = data if isinstance(data, list) else (data.get("quotes") or [])
        fields = ds["fields"]
        quotes = []
        for item in items:
            if not isinstance(item, dict):
                continue
            en = next((item.get(f, "") for f in fields.get("en", []) if item.get(f)), "")
            author = next((item.get(f, "") for f in fields.get("author", []) if item.get(f)), "Khuyết danh")
            en = clean(en)
            if len(en) >= 15:
                quotes.append({"en": en, "author": clean(author) or "Khuyết danh",
                               "topics": [], "_source": f"github_{ds['name']}"})

        print(f"  [GitHub-{ds['name']}] {len(quotes)} quotes")
        all_quotes.extend(quotes)

    cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
    print(f"[GitHub] DONE: {len(all_quotes)} quotes")
    return all_quotes

# ────────────────────────────────────────────────────────────────────────────
# SOURCE 4: wisdomquotes.com
# ────────────────────────────────────────────────────────────────────────────

WISDOM_SLUGS = [
    "life-quotes", "happiness-quotes", "success-quotes", "love-quotes",
    "inspirational-quotes", "motivational-quotes", "friendship-quotes",
    "family-quotes", "attitude-quotes", "change-quotes", "courage-quotes",
    "education-quotes", "faith-quotes", "forgiveness-quotes", "freedom-quotes",
    "funny-quotes", "goal-quotes", "gratitude-quotes", "growth-quotes",
    "hard-work-quotes", "heart-quotes", "hope-quotes", "kindness-quotes",
    "leadership-quotes", "learning-quotes", "loyalty-quotes", "money-quotes",
    "nature-quotes", "patience-quotes", "peace-quotes", "perseverance-quotes",
    "positive-quotes", "purpose-quotes", "relationship-quotes", "respect-quotes",
    "strength-quotes", "time-quotes", "trust-quotes", "truth-quotes",
    "wisdom-quotes", "work-quotes", "mindset-quotes", "failure-quotes",
    "creativity-quotes", "beauty-quotes", "anger-quotes", "loneliness-quotes",
    "grief-quotes", "anxiety-quotes", "confidence-quotes", "discipline-quotes",
]

def crawl_wisdomquotes():
    """Scrape wisdomquotes.com."""
    cache_file = SCRATCHPAD / "wisdomquotes.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        print(f"[WisdomQuotes] Loaded {len(data)} from cache")
        return data

    all_quotes = []
    for i, slug in enumerate(WISDOM_SLUGS):
        url = f"https://wisdomquotes.com/{slug}/"
        r = rate_limited_get(url, delay=1.0)
        if not r:
            continue
        soup = BeautifulSoup(r.text, 'html.parser')
        for bq in soup.select('blockquote'):
            text = bq.text.strip()
            parts = re.split(r'\s*[–—-]\s*(?=[A-Z])', text)
            if len(parts) >= 2:
                quote_text = parts[0].strip().strip('"\'""''')
                author = parts[-1].strip()
            else:
                quote_text = text.strip('"\'""''')
                author = "Khuyết danh"
            quote_text = clean(quote_text)
            if len(quote_text) >= 20:
                all_quotes.append({
                    "en": quote_text,
                    "author": clean(author),
                    "topics": [],
                    "_source": "wisdomquotes",
                })

        if (i + 1) % 10 == 0:
            print(f"  [WisdomQuotes] {i+1}/{len(WISDOM_SLUGS)} → {len(all_quotes)} quotes")

    cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
    print(f"[WisdomQuotes] DONE: {len(all_quotes)} quotes")
    return all_quotes

# ────────────────────────────────────────────────────────────────────────────
# SOURCE 5: quotationspage.com
# ────────────────────────────────────────────────────────────────────────────

QUOTE_PAGE_SUBJECTS = [
    "life", "love", "success", "happiness", "friendship", "wisdom",
    "courage", "education", "time", "money", "death", "family",
    "art", "science", "nature", "politics", "books", "music",
    "humor", "work", "change", "leadership", "truth", "freedom",
    "faith", "hope", "justice", "kindness", "knowledge", "strength",
]

def crawl_quotationspage():
    """Scrape quotationspage.com."""
    cache_file = SCRATCHPAD / "quotationspage.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        print(f"[QuotationsPage] Loaded {len(data)} from cache")
        return data

    all_quotes = []
    for subject in QUOTE_PAGE_SUBJECTS:
        for page in range(1, 6):  # up to 5 pages per subject
            url = f"https://www.quotationspage.com/subjects/{subject}/" if page == 1 \
                else f"https://www.quotationspage.com/subjects/{subject}/{page}.html"
            r = rate_limited_get(url, delay=1.5)
            if not r:
                break
            soup = BeautifulSoup(r.text, 'html.parser')
            # Quotationspage uses dt/dd structure
            dts = soup.select('dt.quote')
            if not dts:
                # Try blockquote
                for bq in soup.select('blockquote, .quote'):
                    text = clean(bq.text)
                    if len(text) >= 20:
                        all_quotes.append({
                            "en": text, "author": "Khuyết danh",
                            "topics": [], "_source": "quotationspage"
                        })
                break

            for dt in dts:
                text = clean(dt.text)
                dd = dt.find_next_sibling('dd')
                author = clean(dd.text) if dd else "Khuyết danh"
                author = re.sub(r'^by\s+', '', author, flags=re.I).strip()
                if len(text) >= 20:
                    all_quotes.append({
                        "en": text, "author": author,
                        "topics": [], "_source": "quotationspage"
                    })

            # Check next page
            if not soup.select_one('a[href*="page"], a.next'):
                break

        print(f"  [QuotationsPage] {subject}: {len(all_quotes)} total so far")

    cache_file.write_text(json.dumps(all_quotes, ensure_ascii=False))
    print(f"[QuotationsPage] DONE: {len(all_quotes)} quotes")
    return all_quotes

# ────────────────────────────────────────────────────────────────────────────
# TRANSLATION
# ────────────────────────────────────────────────────────────────────────────

def batch_translate_text(texts, src, tgt, batch_size=20):
    """Dịch danh sách texts theo batch, trả về list kết quả."""
    if not texts:
        return []

    SEP = " ◈ "
    results = [""] * len(texts)

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        combined = SEP.join(batch)

        # Nếu combined quá dài (>4500 chars), giảm batch_size
        if len(combined) > 4500 and batch_size > 1:
            half = max(1, batch_size // 2)
            sub = batch_translate_text(batch, src, tgt, batch_size=half)
            for j, s in enumerate(sub):
                results[i+j] = s
            continue

        for attempt in range(3):
            try:
                out = GoogleTranslator(source=src, target=tgt).translate(combined)
                if not out:
                    time.sleep(1)
                    continue
                parts = out.split(SEP)
                if len(parts) == len(batch):
                    for j, p in enumerate(parts):
                        results[i+j] = clean(p)
                else:
                    # Mismatch - fallback: translate 1-by-1
                    for j, t in enumerate(batch):
                        try:
                            r = GoogleTranslator(source=src, target=tgt).translate(t)
                            results[i+j] = clean(r) if r else ""
                        except Exception:
                            results[i+j] = ""
                        time.sleep(0.2)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    pass  # Leave as "" for re-translation

        time.sleep(0.3)

    return results

def translate_quotes_file(input_file, output_file):
    """Dịch toàn bộ quotes trong một file."""
    data = json.loads(Path(input_file).read_text())
    print(f"[Translate] {input_file}: {len(data)} quotes")

    need_vi = [(i, q) for i, q in enumerate(data) if q.get("en") and not q.get("vi")]
    need_en = [(i, q) for i, q in enumerate(data) if q.get("vi") and not q.get("en")]

    print(f"  Need VI: {len(need_vi)}, Need EN: {len(need_en)}")

    BATCH = 20
    for start in range(0, len(need_vi), BATCH):
        batch = need_vi[start:start+BATCH]
        texts = [q["en"] for _, q in batch]
        results = batch_translate_text(texts, "en", "vi", batch_size=BATCH)
        for (idx, q), vi in zip(batch, results):
            data[idx]["vi"] = vi
        if start % 500 == 0:
            print(f"  EN→VI: {min(start+BATCH, len(need_vi))}/{len(need_vi)}")
            Path(output_file).write_text(json.dumps(data, ensure_ascii=False))

    for start in range(0, len(need_en), BATCH):
        batch = need_en[start:start+BATCH]
        texts = [q["vi"] for _, q in batch]
        results = batch_translate_text(texts, "vi", "en", batch_size=BATCH)
        for (idx, q), en in zip(batch, results):
            data[idx]["en"] = en
        if start % 500 == 0:
            print(f"  VI→EN: {min(start+BATCH, len(need_en))}/{len(need_en)}")
            Path(output_file).write_text(json.dumps(data, ensure_ascii=False))

    Path(output_file).write_text(json.dumps(data, ensure_ascii=False))
    print(f"[Translate] Done → {output_file}")
    return data

# ────────────────────────────────────────────────────────────────────────────
# DEDUPLICATION & MERGE
# ────────────────────────────────────────────────────────────────────────────

def fingerprint(text):
    t = text.lower().strip()
    t = re.sub(r'\s+', ' ', t)
    t = unicodedata.normalize('NFC', t)
    return t[:150]

def load_existing():
    f = DATA_DIR / "quotes.json"
    data = json.loads(f.read_text())
    en_set = {fingerprint(q.get("en", "")) for q in data if q.get("en")}
    vi_set = {fingerprint(q.get("vi", "")) for q in data if q.get("vi")}
    return data, en_set, vi_set

def deduplicate_and_merge(raw_quotes, existing_data, existing_en, existing_vi):
    """Dedup and merge new quotes with existing."""
    seen_en = set(existing_en)
    seen_vi = set(existing_vi)

    unique = []
    for q in raw_quotes:
        en_fp = fingerprint(q.get("en", ""))
        vi_fp = fingerprint(q.get("vi", ""))

        if not q.get("en") and not q.get("vi"):
            continue
        if q.get("en") and len(q["en"]) < 15:
            continue

        if en_fp and en_fp in seen_en:
            continue
        if vi_fp and vi_fp in seen_vi:
            continue

        if en_fp:
            seen_en.add(en_fp)
        if vi_fp:
            seen_vi.add(vi_fp)

        # Clean internal fields
        q2 = {k: v for k, v in q.items() if not k.startswith("_")}
        if "topics" not in q2:
            q2["topics"] = []
        if not q2.get("author"):
            q2["author"] = "Khuyết danh"
        q2.setdefault("en", "")
        q2.setdefault("vi", "")
        unique.append(q2)

    # Assign IDs
    max_id = max((q.get("id", 0) for q in existing_data), default=0)
    for i, q in enumerate(unique):
        q["id"] = max_id + i + 1

    all_combined = existing_data + unique
    return all_combined, unique

def rebuild_ancillary(all_quotes):
    """Rebuild topics.json, authors.json, meta.json."""
    from collections import Counter, defaultdict

    # Topics
    topic_counts = Counter()
    TOPIC_LABELS = {
        "cuoc-song": "Cuộc sống",
        "tinh-yeu": "Tình yêu",
        "thanh-cong": "Thành công",
        "tinh-ban": "Tình bạn",
        "giao-duc": "Giáo dục",
        "thoi-gian": "Thời gian",
        "su-nghiep": "Sự nghiệp",
        "gia-dinh": "Gia đình",
        "tri-tue": "Trí tuệ",
        "tam-hon": "Tâm hồn",
        "trai-tim": "Trái tim",
        "tieng-anh": "Tiếng Anh",
        "thay-doi": "Thay đổi",
        "yeu-nuoc": "Yêu nước",
        "van-minh-khoa-hoc": "Văn minh & Khoa học",
        "song-chet": "Sống & Chết",
        "nhung-trich-dan-hay": "Trích dẫn hay",
        "nhung-manh-ngon-tinh": "Mảnh ngôn tình",
    }
    for q in all_quotes:
        for t in q.get("topics", []):
            topic_counts[t] += 1
    topics_json = {
        slug: {"label": TOPIC_LABELS.get(slug, slug), "count": cnt}
        for slug, cnt in topic_counts.items()
    }
    (DATA_DIR / "topics.json").write_text(
        json.dumps(topics_json, ensure_ascii=False, indent=2))

    # Authors
    author_counts = Counter(q.get("author", "Khuyết danh") for q in all_quotes)
    authors_json = [
        {"name": name, "count": cnt}
        for name, cnt in author_counts.most_common()
    ]
    (DATA_DIR / "authors.json").write_text(
        json.dumps(authors_json, ensure_ascii=False, indent=2))

    # Meta
    meta = {
        "schemaVersion": 1,
        "totalQuotes": len(all_quotes),
        "totalAuthors": len(author_counts),
        "totalTopics": len(topics_json),
        "withEnglish": sum(1 for q in all_quotes if q.get("en")),
        "withVietnamese": sum(1 for q in all_quotes if q.get("vi")),
        "source": "mixed (azquotes, wikiquote, github datasets, web scraping)",
    }
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    return meta

# ────────────────────────────────────────────────────────────────────────────
# MAIN COMMANDS
# ────────────────────────────────────────────────────────────────────────────

def cmd_crawl_azquotes(args):
    letters = args.letters or "abcdefghijklmnopqrstuvwxyz"
    crawl_azquotes(letters=letters, max_authors=args.max_authors)

def cmd_crawl_wikiquote_en(args):
    crawl_wikiquote_lang("en", title_from=args.title_from, title_to=args.title_to)

def cmd_crawl_wikiquote_vi(args):
    crawl_wikiquote_lang("vi")

def cmd_crawl_other(args):
    crawl_github_datasets()
    crawl_wisdomquotes()
    crawl_quotationspage()

def cmd_translate(args):
    infile = args.input or str(SCRATCHPAD / "merged_raw.json")
    outfile = args.output or str(SCRATCHPAD / "merged_translated.json")
    translate_quotes_file(infile, outfile)

def cmd_merge(args):
    """Gộp tất cả raw files → translate → write to data/."""
    print("[Merge] Loading existing quotes...")
    existing_data, existing_en, existing_vi = load_existing()
    print(f"[Merge] Existing: {len(existing_data)} quotes")

    # Tập hợp tất cả raw crawled files
    raw_files = list(SCRATCHPAD.glob("azquotes_*.json")) + \
                list(SCRATCHPAD.glob("wq_en_quotes_*.json")) + \
                list(SCRATCHPAD.glob("wq_vi_quotes_*.json")) + \
                [SCRATCHPAD / "github_all.json",
                 SCRATCHPAD / "wisdomquotes.json",
                 SCRATCHPAD / "quotationspage.json"]

    all_raw = []
    for f in raw_files:
        if f.exists():
            data = json.loads(f.read_text())
            print(f"  {f.name}: {len(data)} quotes")
            all_raw.extend(data)

    print(f"[Merge] Total raw: {len(all_raw)}")

    # Dedup raw first (always, so we can compare count against cached translation)
    raw_file = SCRATCHPAD / "merged_raw.json"
    _, existing_en_copy, existing_vi_copy = load_existing()
    seen_en = set(existing_en_copy)
    seen_vi = set(existing_vi_copy)
    deduped_raw = []
    for q in all_raw:
        en_fp = fingerprint(q.get("en", ""))
        vi_fp = fingerprint(q.get("vi", ""))
        if en_fp and en_fp in seen_en:
            continue
        if vi_fp and vi_fp in seen_vi:
            continue
        if en_fp:
            seen_en.add(en_fp)
        if vi_fp:
            seen_vi.add(vi_fp)
        deduped_raw.append(q)

    print(f"[Merge] After initial dedup: {len(deduped_raw)}")
    raw_file.write_text(json.dumps(deduped_raw, ensure_ascii=False))

    # Check if translated version exists
    trans_file = SCRATCHPAD / "merged_translated.json"
    trans_meta_file = SCRATCHPAD / "merged_translated_meta.json"
    force_translate = getattr(args, "force_translate", False)
    if trans_file.exists() and not force_translate:
        translated = json.loads(trans_file.read_text())
        # Check content hash: compare raw deduped count against cached metadata
        cached_raw_count = None
        if trans_meta_file.exists():
            try:
                cached_raw_count = json.loads(trans_meta_file.read_text()).get("raw_count")
            except Exception:
                pass
        if cached_raw_count is not None and cached_raw_count != len(deduped_raw):
            print(
                f"[Merge] WARNING: cached translation has raw_count={cached_raw_count} "
                f"but current deduped raw has {len(deduped_raw)} quotes. "
                f"New quotes may be missing from translation. "
                f"Run with --force-translate to re-translate.",
                file=sys.stderr,
            )
        elif cached_raw_count is None:
            print(
                "[Merge] WARNING: no raw_count metadata for cached translation. "
                "Cannot verify cache freshness. Run with --force-translate to be safe.",
                file=sys.stderr,
            )
        print(f"[Merge] Using pre-translated: {len(translated)} quotes")
    else:
        if force_translate and trans_file.exists():
            print("[Merge] --force-translate: ignoring cached translation, re-translating...")
        if not args.skip_translate:
            print("[Merge] Translating...")
            translated = translate_quotes_file(str(raw_file), str(trans_file))
            # Write metadata so future runs can detect stale cache
            trans_meta_file.write_text(
                json.dumps({"raw_count": len(deduped_raw)}, ensure_ascii=False)
            )
        else:
            translated = deduped_raw
            print("[Merge] Skipping translation (--skip-translate)")

    # Final dedup and merge
    print("[Merge] Final dedup and merge...")
    all_combined, new_quotes = deduplicate_and_merge(
        translated, existing_data, existing_en, existing_vi
    )

    print(f"[Merge] Writing {len(all_combined)} total quotes...")
    (DATA_DIR / "quotes.json").write_text(
        json.dumps(all_combined, ensure_ascii=False, indent=2))
    (DATA_DIR / "quotes.min.json").write_text(
        json.dumps(all_combined, ensure_ascii=False, separators=(',', ':')))

    meta = rebuild_ancillary(all_combined)

    print("\n" + "=" * 60)
    print(f"MERGE COMPLETE:")
    print(f"  Total quotes: {meta['totalQuotes']}")
    print(f"  New quotes added: {len(new_quotes)}")
    print(f"  With English: {meta['withEnglish']}")
    print(f"  With Vietnamese: {meta['withVietnamese']}")
    print(f"  Total authors: {meta['totalAuthors']}")
    print("=" * 60)

def cmd_all(args):
    """Chạy toàn bộ pipeline."""
    print("=== FULL PIPELINE ===\n")

    print("\n--- Phase 1: Crawling AZQuotes ---")
    crawl_azquotes()

    print("\n--- Phase 2: Crawling Wikiquote EN ---")
    crawl_wikiquote_lang("en")

    print("\n--- Phase 3: Crawling Wikiquote VI ---")
    crawl_wikiquote_lang("vi")

    print("\n--- Phase 4: GitHub & other sources ---")
    crawl_github_datasets()
    crawl_wisdomquotes()
    crawl_quotationspage()

    print("\n--- Phase 5: Merge & Translate ---")
    args.skip_translate = False
    cmd_merge(args)

def main():
    parser = argparse.ArgumentParser(description="Quote crawler & translator")
    sub = parser.add_subparsers(dest="cmd")

    p_azq = sub.add_parser("azquotes", help="Crawl AZQuotes")
    p_azq.add_argument("--letters", default="abcdefghijklmnopqrstuvwxyz")
    p_azq.add_argument("--max-authors", type=int, default=None)

    p_wqen = sub.add_parser("wikiquote-en", help="Crawl English Wikiquote")
    p_wqen.add_argument("--title-from", default=None)
    p_wqen.add_argument("--title-to", default=None)

    p_wqvi = sub.add_parser("wikiquote-vi", help="Crawl Vietnamese Wikiquote")

    p_other = sub.add_parser("other", help="Crawl GitHub & other sources")

    p_trans = sub.add_parser("translate", help="Translate quotes file")
    p_trans.add_argument("--input", default=None)
    p_trans.add_argument("--output", default=None)

    p_merge = sub.add_parser("merge", help="Merge all crawled data")
    p_merge.add_argument("--skip-translate", action="store_true")
    p_merge.add_argument("--force-translate", action="store_true",
                         help="Ignore cached merged_translated.json and re-translate")

    p_all = sub.add_parser("all", help="Run full pipeline")

    args = parser.parse_args()

    if args.cmd == "azquotes":
        cmd_crawl_azquotes(args)
    elif args.cmd == "wikiquote-en":
        cmd_crawl_wikiquote_en(args)
    elif args.cmd == "wikiquote-vi":
        cmd_crawl_wikiquote_vi(args)
    elif args.cmd == "other":
        cmd_crawl_other(args)
    elif args.cmd == "translate":
        cmd_translate(args)
    elif args.cmd == "merge":
        cmd_merge(args)
    elif args.cmd == "all":
        cmd_all(args)
    else:
        # Default: run all
        class DefaultArgs:
            skip_translate = False
            force_translate = False
        cmd_all(DefaultArgs())

if __name__ == "__main__":
    main()
