import feedparser
import json
import hashlib
import os
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
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "lang": "zh",
    },
    {
        "name": "虎嗅",
        "url": "https://www.huxiu.com/rss/0.xml",
        "lang": "zh",
    },
]

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

            items.append({
                "id": item_id,
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "link": entry.get("link", ""),
                "published": pub_iso,
                "source": source["name"],
                "lang": source["lang"],
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

    all_news.sort(key=lambda x: x["published"], reverse=True)

    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_news)} news items to {NEWS_FILE}")

if __name__ == "__main__":
    main()
