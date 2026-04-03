import feedparser
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RSS feeds grouped by category
RSS_FEEDS: dict[str, tuple[str, str]] = {
    # --- Technology ---
    "TechCrunch":        ("Technology", "https://techcrunch.com/feed/"),
    "Wired Tech":        ("Technology", "https://www.wired.com/feed/category/tech/latest/rss"),

    # --- Business & Finance (Global) ---
    "CNBC Top News":     ("Business & Finance", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    "WSJ Business":      ("Business & Finance", "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"),
    "Reuters Finance":   ("Business & Finance", "https://feeds.reuters.com/reuters/businessNews"),

    # --- India Finance ---
    "Economic Times Markets": ("India Finance", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    "Moneycontrol":      ("India Finance", "https://www.moneycontrol.com/rss/latestnews.xml"),

    # --- India Policy & Government ---
    "LiveMint":          ("India Policy", "https://www.livemint.com/rss/news"),
    "Business Standard": ("India Policy", "https://www.business-standard.com/rss/home_page_top_stories.rss"),
    "PIB India":         ("India Policy", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"),
}

CATEGORY_COLORS: dict[str, str] = {
    "Technology":        "#0f9d58",
    "Business & Finance":"#1a73e8",
    "India Finance":     "#e65100",
    "India Policy":      "#880e4f",
}


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def fetch_daily_news(max_articles_per_feed: int = 4) -> list[dict]:
    all_news = []
    seen_titles: set[str] = set()

    for source, (category, url) in RSS_FEEDS.items():
        logger.info(f"Fetching from {source} ({category})...")
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                logger.warning(f"Feed parse error for {source}: {feed.bozo_exception}")
                continue

            for entry in feed.entries[:max_articles_per_feed]:
                title = entry.get("title", "").strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                summary = clean_html(entry.get("summary", ""))
                link = entry.get("link", "")

                all_news.append({
                    "source": source,
                    "category": category,
                    "title": title,
                    "summary": summary,
                    "link": link,
                })

        except Exception as e:
            logger.error(f"Failed to fetch {source}: {e}")

    logger.info(f"Fetched {len(all_news)} unique articles from {len(RSS_FEEDS)} feeds.")
    return all_news


if __name__ == "__main__":
    news = fetch_daily_news(max_articles_per_feed=2)
    for n in news:
        print(f"[{n['category']}] [{n['source']}] {n['title']}")
