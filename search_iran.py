import json
import re
import urllib.request
import urllib.parse
from datetime import datetime


def hash_code(s):
    hash_val = 0
    for char in s:
        hash_val = (hash_val << 5) - hash_val + ord(char)
        hash_val = hash_val & hash_val
    return abs(hash_val)


def parse_gdelt_date(date_str):
    if not date_str:
        return datetime.now()
    try:
        match = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$", date_str)
        if match:
            year, month, day, hour, minute, second = match.groups()
            return datetime(
                int(year), int(month), int(day), int(hour), int(minute), int(second)
            )
    except:
        pass
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.now()


def transform_gdelt_article(article, category, source, index):
    title = article.get("title", "")
    alert_keywords = ["breaking", "urgent", "alert", "crisis", "emergency", "warn"]
    is_alert = any(keyword in title.lower() for keyword in alert_keywords)
    url = article.get("url", "")
    url_hash = hash_code(url) if url else str(index)
    unique_id = f"gdelt-{category}-{url_hash}-{index}"
    seendate = article.get("seendate", "")
    timestamp = parse_gdelt_date(seendate)
    return {
        "id": unique_id,
        "title": title,
        "link": url,
        "pubDate": seendate,
        "timestamp": timestamp.timestamp() * 1000,
        "source": source or article.get("domain", "Unknown"),
        "category": category,
        "isAlert": is_alert,
        "alertKeyword": None,
        "region": None,
        "topics": [],
    }


def fetch_category_news(category):
    category_queries = {
        "politics": "(politics OR government OR election OR congress)",
        "tech": '(technology OR software OR startup OR "silicon valley")',
        "finance": '(finance OR "stock market" OR economy OR banking)',
        "gov": '("federal government" OR "white house" OR congress OR regulation)',
        "ai": '("artificial intelligence" OR "machine learning" OR AI OR ChatGPT)',
        "intel": "(intelligence OR security OR military OR defense)",
    }
    try:
        base_query = category_queries[category]
        full_query = f"{base_query} sourcelang:english"
        encoded_query = urllib.parse.quote(full_query)
        gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&timespan=7d&mode=artlist&maxrecords=10&format=json&sort=date"
        print(f"Fetching {category} news...")
        with urllib.request.urlopen(gdelt_url, timeout=10) as response:
            if response.status != 200:
                print(f"HTTP {response.status}: {response.reason}")
                return []
            data = json.loads(response.read().decode())
            if not data or "articles" not in data:
                return []
            feeds = {
                "politics": ["BBC World", "NPR News", "Guardian World", "NYT World"],
                "tech": [
                    "Hacker News",
                    "Ars Technica",
                    "The Verge",
                    "MIT Tech Review",
                    "ArXiv AI",
                    "OpenAI Blog",
                ],
                "finance": [
                    "CNBC",
                    "MarketWatch",
                    "Yahoo Finance",
                    "BBC Business",
                    "FT",
                ],
                "gov": [
                    "White House",
                    "Federal Reserve",
                    "SEC Announcements",
                    "DoD News",
                ],
                "ai": ["OpenAI Blog", "ArXiv AI"],
                "intel": ["CSIS", "Brookings"],
            }
            category_feeds = feeds.get(category, [])
            default_source = category_feeds[0] if category_feeds else "News"
            news_items = []
            for i, article in enumerate(data["articles"]):
                news_item = transform_gdelt_article(
                    article, category, article.get("domain", default_source), i
                )
                news_items.append(news_item)
            return news_items
    except Exception as e:
        print(f"Error fetching {category} news: {e}")
        return []


def search_iran_news():
    print("Searching for Iran-related news...")
    all_news = {}
    categories = ["politics", "tech", "finance", "gov", "ai", "intel"]
    for category in categories:
        all_news[category] = fetch_category_news(category)

    iran_news = []
    for category, items in all_news.items():
        for item in items:
            title_lower = item["title"].lower()
            if (
                "iran" in title_lower
                or "tehran" in title_lower
                or "irgc" in title_lower
            ):
                iran_news.append((category, item))

    print(f"Found {len(iran_news)} Iran-related news items:")
    for category, item in iran_news[:5]:
        print(f"[{category.upper()}] {item['title']}")
        print(f"  Source: {item['source']}")
        print(
            f"  Time: {datetime.fromtimestamp(item['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        if item["isAlert"]:
            print(f"  🚨 ALERT")
        print()


if __name__ == "__main__":
    search_iran_news()
