#!/usr/bin/env python3
"""
Simple script to fetch news from situation-monitor API
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime


def hash_code(s):
    """Simple hash function to generate unique IDs from URLs"""
    hash_val = 0
    for char in s:
        hash_val = (hash_val << 5) - hash_val + ord(char)
        hash_val = hash_val & hash_val  # Convert to 32bit integer
    return abs(hash_val)


def parse_gdelt_date(date_str):
    """Parse GDELT date format (20251202T224500Z) to datetime"""
    if not date_str:
        return datetime.now()
    try:
        # Convert 20251202T224500Z to 2025-12-02T22:45:00Z
        match = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$", date_str)
        if match:
            year, month, day, hour, minute, second = match.groups()
            return datetime(
                int(year), int(month), int(day), int(hour), int(minute), int(second)
            )
    except:
        pass
    # Fallback to standard parsing
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.now()
    try:
        # Convert 20251202T224500Z to 2025-12-02T22:45:00Z
        match = date_str.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$")
        if match:
            year, month, day, hour, minute, second = match.groups()
            return datetime(
                int(year), int(month), int(day), int(hour), int(minute), int(second)
            )
    except:
        pass
    # Fallback to standard parsing
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.now()


def transform_gdelt_article(article, category, source, index):
    """Transform GDELT article to news item"""
    title = article.get("title", "")

    # Simple alert detection (keywords that might indicate importance)
    alert_keywords = ["breaking", "urgent", "alert", "crisis", "emergency", "warn"]
    is_alert = any(keyword in title.lower() for keyword in alert_keywords)

    # Generate unique ID
    url = article.get("url", "")
    url_hash = hash_code(url) if url else str(index)
    unique_id = f"gdelt-{category}-{url_hash}-{index}"

    # Parse date
    seendate = article.get("seendate", "")
    timestamp = parse_gdelt_date(seendate)

    return {
        "id": unique_id,
        "title": title,
        "link": url,
        "pubDate": seendate,
        "timestamp": timestamp.timestamp() * 1000,  # Convert to milliseconds
        "source": source or article.get("domain", "Unknown"),
        "category": category,
        "isAlert": is_alert,
        "alertKeyword": None,
        "region": None,
        "topics": [],
    }


def fetch_category_news(category):
    """Fetch news for a specific category using GDELT via proxy"""
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

        # URL encode the query
        encoded_query = urllib.parse.quote(full_query)
        gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&timespan=7d&mode=artlist&maxrecords=10&format=json&sort=date"

        print(f"Fetching {category} news from GDELT...")

        # Make request
        with urllib.request.urlopen(gdelt_url, timeout=10) as response:
            if response.status != 200:
                print(f"HTTP {response.status}: {response.reason}")
                return []

            # Read and parse response
            data = json.loads(response.read().decode())

            if not data or "articles" not in data:
                return []

            # Get source names for this category
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

            # Transform articles
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


def fetch_all_news():
    """Fetch all news categories"""
    categories = ["politics", "tech", "finance", "gov", "ai", "intel"]
    result = {}

    for category in categories:
        result[category] = fetch_category_news(category)

    return result


def main():
    """Main function to fetch and display news"""
    print("Fetching financial news from situation-monitor...\n")

    news = fetch_all_news()

    total_items = sum(len(items) for items in news.values())
    print(f"Fetched news from {len(news)} categories")
    print(f"Total news items: {total_items}\n")

    # Display news from each category
    for category, items in news.items():
        if items:
            print(f"=== {category.upper()} NEWS ===")
            for i, item in enumerate(items[:3]):  # Show top 3 items
                print(f"{i + 1}. {item['title']}")
                print(f"   Source: {item['source']}")
                print(
                    f"   Time: {datetime.fromtimestamp(item['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')}"
                )
                if item["isAlert"]:
                    print(f"   🚨 ALERT: {item['alertKeyword']}")
                print()
        else:
            print(f"=== {category.upper()} NEWS ===")
            print("No news available\n")


if __name__ == "__main__":
    main()
