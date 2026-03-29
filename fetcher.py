import feedparser
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A curated list of free RSS feeds covering Tech, Finance, and Business
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "WSJ Business": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "Wired Tech": "https://www.wired.com/feed/category/tech/latest/rss"
}

def clean_html(raw_html):
    """Remove HTML tags from summary texts."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_daily_news(max_articles_per_feed=5):
    """
    Fetch the top news from the defined RSS feeds.
    Returns a list of dictionaries containing title, summary, link, and source.
    """
    all_news = []
    
    for source, url in RSS_FEEDS.items():
        logger.info(f"Fetching news from {source}...")
        try:
            feed = feedparser.parse(url)
            # Some feeds might fail to parse over network issues
            if feed.bozo and hasattr(feed.bozo_exception, 'getMessage'):
                logger.warning(f"Error parsing feed {source}: {feed.bozo_exception}")
                
            entries = feed.entries[:max_articles_per_feed]
            for entry in entries:
                title = entry.get("title", "")
                summary_html = entry.get("summary", "")
                link = entry.get("link", "")
                summary = clean_html(summary_html)
                
                # We only add it if it has a title
                if title:
                    all_news.append({
                        "source": source,
                        "title": title,
                        "summary": summary,
                        "link": link
                    })
        except Exception as e:
            logger.error(f"Failed to fetch {source}: {e}")

    logger.info(f"Successfully fetched {len(all_news)} articles total.")
    return all_news

if __name__ == "__main__":
    # Test fetcher
    news = fetch_daily_news(max_articles_per_feed=2)
    for n in news:
        print(f"[{n['source']}] {n['title']}\n{n['summary'][:100]}...\n{n['link']}\n")
