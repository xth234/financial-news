import feedparser
import json
import hashlib
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from html import unescape

RSS_SOURCES = [
    {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "lang": "en"},
    {"name": "CNBC Top News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "lang": "en"},
    {"name": "东方财富", "url": "https://finance.eastmoney.com/rss/soft/7_88888888.xml", "lang": "zh"},
    {"name": "虎嗅", "url": "https://www.huxiu.com/rss/0.xml", "lang": "zh"},
    {"name": "律动BlockBeats", "url": "https://api.theblockbeats.news/v2/rss/all", "lang": "zh"},
]

CATEGORIES = {
    "AI": ["ai", "artificial intelligence", "machine learning", "deep learning", "chatgpt", "gpt", "llm", "large language model", "neural network", "openai", "claude", "gemini", "copilot", "transformer", "人工智能", "大模型", "机器学习", "深度学习", "ai大模型"],
    "区块链": ["blockchain", "bitcoin", "ethereum", "crypto", "cryptocurrency", "web3", "defi", "nft", "solana", "smart contract", "token", "区块链", "比特币", "以太坊", "加密货币", "数字货币"],
    "黄金": ["gold", "gold price", "precious metal", "黄金", "金价", "贵金属", "金条", "金市"],
    "地缘": ["geopolitics", "geopolitical", "war", "conflict", "sanctions", "military", "defense", "oil price", "crude", "supply chain", "tariff", "trade war", "中东", "俄罗斯", "乌克兰", "地缘", "战争", "冲突", "制裁", "军事", "国防", "油价", "通胀", "供应链", "关税", "贸易战", "原油"],
}

def classify(text):
    lower = text.lower()
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw.lower() in lower:
                return cat
    return None

def translate_en_to_zh(text):
    if not text or len(text.strip()) < 10:
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="zh-CN").translate(text[:5000])
    except:
        return text

def extract_article(url, timeout=15):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "form", "button", "svg", "iframe"]):
            tag.decompose()

        img_html = ""
        for meta in soup.find_all("meta"):
            prop = (meta.get("property") or meta.get("name") or "").lower()
            if prop in ("og:image", "twitter:image"):
                src = meta.get("content", "")
                if src and not src.startswith("data:"):
                    img_html = f'<div class="article-image"><img src="{src}" style="max-width:100%;border-radius:8px;margin-bottom:1rem;" /></div>'
                    break
        if not img_html:
            img = soup.find("img")
            if img and img.get("src") and not img["src"].startswith("data:"):
                img_html = f'<div class="article-image"><img src="{img["src"]}" style="max-width:100%;border-radius:8px;margin-bottom:1rem;" /></div>'

        selectors = ["article", "[role=main]", "main", ".article-body", ".story-body", ".post-content", "#article-content", ".content", ".article", "#story-body", ".story-body__inner", ".article__body", ".article-content", ".entry-content", ".post-body"]
        container = None
        for sel in selectors:
            container = soup.select_one(sel)
            if container:
                break

        if not container:
            ps = soup.find_all("p")
            body = "".join(str(p) for p in ps if len(p.get_text(strip=True)) > 30)
            return img_html + body if body else None

        for tag in container(["script", "style", "nav", "header", "footer", "aside", "noscript", "button", "svg"]):
            tag.decompose()

        parts = []
        for el in container.children:
            if el.name in ("p", "h2", "h3", "h4", "li", "blockquote", "ul", "ol", "img", "figure", "div"):
                text = el.get_text(strip=True) if el.name != "img" else ""
                if el.name == "img" and el.get("src"):
                    parts.append(f'<p><img src="{el["src"]}" style="max-width:100%;border-radius:8px;" /></p>')
                elif el.name in ("h2", "h3", "h4"):
                    if len(text) > 5:
                        parts.append(f"<{el.name}>{text}</{el.name}>")
                elif el.name == "blockquote" and len(text) > 10:
                    parts.append(f"<blockquote style='border-left:3px solid #facc15;padding-left:1rem;margin:0.5rem 0;color:#94a3b8;'>{text}</blockquote>")
                elif el.name in ("ul", "ol"):
                    lis = []
                    for li in el.find_all("li", recursive=False):
                        t = li.get_text(strip=True)
                        if len(t) > 10:
                            lis.append(f"<li>{t}</li>")
                    if lis:
                        parts.append(f"<{el.name}>{''.join(lis)}</{el.name}>")
                elif el.name == "p" and len(text) > 20:
                    parts.append(f"<p>{text}</p>")
                elif el.name == "div" and el.get("class"):
                    t = el.get_text(strip=True)
                    if len(t) > 50:
                        parts.append(f"<p>{t}</p>")

        content = "\n".join(parts[:60])
        if not content:
            ps = soup.find_all("p")
            body = "".join(f"<p>{p.get_text(strip=True)}</p>" for p in ps if len(p.get_text(strip=True)) > 30)
            content = body
        content = unescape(content)
        return (img_html + content) if content else None
    except Exception as e:
        print(f"  Scrape failed: {type(e).__name__}")
        return None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NEWS_FILE = DATA_DIR / "news.json"

def fetch_rss(source, existing_ids):
    items = []
    try:
        feed = feedparser.parse(source["url"])
        entries = [e for e in feed.entries if hashlib.md5(e.link.encode()).hexdigest()[:12] not in existing_ids][:10]
        print(f"  {len(entries)} new from {source['name']}")
        for i, entry in enumerate(entries):
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:300]
            if not classify(title + " " + summary):
                continue

            print(f"  [{i+1}/{len(entries)}] {title[:60]}...")

            rss_content = ""
            if hasattr(entry, "content") and entry.content:
                rss_content = entry.content[0].get("value", "")
            elif hasattr(entry, "description") and entry.description:
                rss_content = entry.description

            if len(rss_content) > 500:
                content = rss_content
            else:
                scraped = extract_article(entry.link)
                content = scraped if scraped else (rss_content if len(rss_content) > 100 else summary)

            if source["lang"] == "en":
                content = translate_en_to_zh(content)

            item_id = hashlib.md5(entry.link.encode()).hexdigest()[:12]
            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                pub_iso = pub_dt.isoformat()
            else:
                pub_iso = datetime.now(timezone.utc).isoformat()

            items.append({
                "id": item_id,
                "title": translate_en_to_zh(title) if source["lang"] == "en" else title,
                "content": content[:10000],
                "link": entry.link,
                "published": pub_iso,
                "source": source["name"],
                "categories": [classify(title + " " + summary)],
            })
            time.sleep(1.5)
    except Exception as e:
        print(f"  Error: {e}")
    return items

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = {}
    if NEWS_FILE.exists():
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            for item in json.load(f):
                existing[item["id"]] = item

    all_new = []
    for source in RSS_SOURCES:
        print(f"Fetching {source['name']}...")
        all_new.extend(fetch_rss(source, set(existing.keys())))

    print(f"\nNew: {len(all_new)}")
    for item in all_new:
        existing[item["id"]] = item

    all_news = sorted(existing.values(), key=lambda x: x["published"], reverse=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    all_news = [n for n in all_news if datetime.fromisoformat(n["published"].replace("Z", "+00:00")) > cutoff]

    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_news)} items")

if __name__ == "__main__":
    main()
