import time
import schedule
import logging
from fetcher import fetch_daily_news
from analyzer import analyze_business_implications
from reporter import generate_markdown_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_news_analyzer_pipeline():
    """Runs the full pipeline: Fetch -> Analyze -> Report"""
    logger.info("Starting Daily News Analyzer Pipeline...")
    
    # Step 1: Fetch
    logger.info("Step 1: Fetching top news from RSS feeds...")
    articles = fetch_daily_news()
    if not articles:
        logger.warning("No articles fetched today. Aborting pipeline.")
        return

    # Step 2: Analyze
    logger.info("Step 2: Passing news to LLM to extract business implications...")
    analysis_text = analyze_business_implications(articles)

    # Step 3: Report
    logger.info("Step 3: Generating final markdown report...")
    report_file = generate_markdown_report(analysis_text, articles)
    
    logger.info(f"Pipeline finished! Report generated successfully at: {report_file}")

if __name__ == "__main__":
    # To run once immediately during testing, we call the pipeline directly:
    print("Running pipeline once immediately for demo purposes...")
    run_news_analyzer_pipeline()
    
    # ---------------------------------------------------------
    # Production Scheduling Logic
    # ---------------------------------------------------------
    # Uncomment the following to run as a true background agent:
    # 
    # SCHEDULE_TIME = "08:00" # Runs every day at 8:00 AM
    #
    # logger.info(f"Setting daily schedule to run at {SCHEDULE_TIME}")
    # schedule.every().day.at(SCHEDULE_TIME).do(run_news_analyzer_pipeline)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60) # check every minute
