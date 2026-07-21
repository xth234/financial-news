import feedparser
import json
import hashlib
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup

RSS_SOURCES = [
    {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "lang": "en"},
    {"name": "CNBC Top News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "lang": "en"},
    {"name": "东方财富", "url": "https://finance.eastmoney.com/rss/soft/7_88888888.xml", "lang": "zh"},
    {"name": "虎嗅", "url": "https://www.huxiu.com/rss/0.xml", "lang": "zh"},
]

CATEGORIES = {
    "AI": ["ai", "artificial intelligence", "machine learning", "deep learning", "chatgpt", "gpt", "llm", "large language model", "neural network", "openai", "claude", "gemini", "copilot", "transformer", "人工智能", "大模型", "机器学习", "深度学习", "ai大模型"],
    "区块链": ["blockchain", "bitcoin", "ethereum", "crypto", "cryptocurrency", "web3", "defi", "nft", "solana", "smart contract", "token", "区块链", "比特币", "以太坊", "加密货币", "数字货币"],
    "黄金": ["gold", "gold price", "precious metal", "黄金", "金价", "贵金属", "金条", "金市"],
    "机器人": ["robot", "robotics", "humanoid", "automation", "autonomous", "boston dynamics", "tesla bot", "optimus", "机器人", "人形机器人", "自动化", "仿生", "机器狗"],
    "科技股": ["nvidia", "nvda", "apple", "aapl", "microsoft", "msft", "google", "googl", "amazon", "amzn", "meta", "tesla", "tsla", "semiconductor", "chip", "big tech", "magnificent seven", "mag7", "科技股", "半导体", "芯片", "纳斯达克", "纳指", "美股"],
    "地缘": ["geopolitics", "geopolitical", "war", "conflict", "sanctions", "military", "defense", "oil price", "crude", "supply chain", "tariff", "trade war", "中东", "俄罗斯", "乌克兰", "地缘", "战争", "冲突", "制裁", "军事", "国防", "油价", "通胀", "供应链", "关税", "贸易战", "原油"],
    "美债": ["treasury yield", "bond yield", "10-year yield", "fed rate", "interest rate", "federal reserve", "yield curve", "fed", "国债", "收益率", "美债", "美联储", "加息", "降息", "利率"],
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

def extract_article(url, timeout=12):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        img = soup.find("meta", property="og:image") or soup.find("img")
        img_html = ""
        if img:
            src = img.get("content") or img.get("src", "")
            if src and not src.startswith("data:"):
                img_html = f'<div class="article-image"><img src="{src}" alt="" style="max-width:100%;border-radius:8px;margin-bottom:1rem;" /></div>'

        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if len(l) > 40]
        content = "\n\n".join(lines[:30])
        content = content.replace("\n", "</p><p>")
        content = f"<p>{content}</p>"
        return img_html + content
    except:
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
            summary = (entry.get("summary") or "")[:300]
            if not classify(title + " " + summary):
                continue

            print(f"  [{i+1}/{len(entries)}] {title[:60]}...")

            has_full = hasattr(entry, "content") and entry.content
            if has_full:
                content = entry.content[0].get("value", summary)
            else:
                content = extract_article(entry.link) or summary

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
            time.sleep(1)
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
