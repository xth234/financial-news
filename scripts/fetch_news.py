import feedparser
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

RSS_SOURCES = [
    {
        "name": "BBC Business",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "lang": "en",
    },
    {
        "name": "CNBC Top News",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "lang": "en",
    },
    {
        "name": "Reuters Business",
        "url": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "lang": "en",
    },
    {
        "name": "华尔街日报",
        "url": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
        "lang": "en",
    },
    {
        "name": "东方财富",
        "url": "https://finance.eastmoney.com/rss/soft/7_88888888.xml",
        "lang": "zh",
    },
    {
        "name": "虎嗅",
        "url": "https://www.huxiu.com/rss/0.xml",
        "lang": "zh",
    },
]

CATEGORIES = {
    "AI": [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "chatgpt", "gpt", "llm", "large language model", "neural network",
        "openai", "claude", "gemini", "copilot", "transformer",
        "人工智能", "大模型", "机器学习", "深度学习", "ai大模型",
    ],
    "区块链": [
        "blockchain", "bitcoin", "ethereum", "crypto", "cryptocurrency",
        "web3", "defi", "nft", "solana", "smart contract", "token",
        "区块链", "比特币", "以太坊", "加密货币", "数字货币",
    ],
    "黄金": [
        "gold", "gold price", "precious metal",
        "黄金", "金价", "贵金属", "金条", "金市",
    ],
    "机器人": [
        "robot", "robotics", "humanoid", "automation", "autonomous",
        "boston dynamics", "tesla bot", "optimus", "机器",
        "机器人", "人形机器人", "自动化", "仿生", "机器狗",
    ],
    "科技股": [
        "nvidia", "nvda", "apple", "aapl", "microsoft", "msft",
        "google", "googl", "amazon", "amzn", "meta", "tesla", "tsla",
        "semiconductor", "chip", "big tech", "magnificent seven", "mag7",
        "科技股", "半导体", "芯片", "纳斯达克", "纳指", "美股",
    ],
}

ALL_KEYWORDS = [kw for kws in CATEGORIES.values() for kw in kws]
KEYWORD_PATTERN = re.compile("|".join(re.escape(k) for k in ALL_KEYWORDS), re.IGNORECASE)

def translate_en_to_zh(text):
    if not text or len(text.strip()) < 10:
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="zh-CN").translate(text[:5000])
    except Exception as e:
        print(f"Translation failed: {e}")
        return text
    matched = []
    lower = text.lower()
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw.lower() in lower:
                matched.append(cat)
                break
    return matched

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NEWS_FILE = DATA_DIR / "news.json"

def fetch_rss(source):
    items = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:15]:
            item_id = hashlib.md5(entry.link.encode()).hexdigest()[:12]
            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                pub_iso = pub_dt.isoformat()
            else:
                pub_iso = datetime.now(timezone.utc).isoformat()

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if source["lang"] == "en":
                summary = translate_en_to_zh(summary)
            text = title + " " + summary
            cats = classify(text)
            if not cats:
                continue
            items.append({
                "id": item_id,
                "title": title,
                "summary": summary,
                "link": entry.get("link", ""),
                "published": pub_iso,
                "source": source["name"],
                "lang": source["lang"],
                "categories": cats,
            })
    except Exception as e:
        print(f"Failed to fetch {source['name']}: {e}")
    return items

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_news = []
    for source in RSS_SOURCES:
        print(f"Fetching {source['name']}...")
        all_news.extend(fetch_rss(source))

    print(f"Filtered to {len(all_news)} relevant items")

    all_news.sort(key=lambda x: x["published"], reverse=True)

    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_news)} news items to {NEWS_FILE}")

if __name__ == "__main__":
    main()
