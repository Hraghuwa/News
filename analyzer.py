import os
import logging
from typing import List, Dict
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def filter_recent_news(articles: List[Dict]) -> str:
    """Combine articles into a single prompt string."""
    news_string = "Today's Top News Articles:\n\n"
    for i, a in enumerate(articles, 1):
        news_string += f"[{i}] {a['title']} (Source: {a['source']})\n"
        news_string += f"Details: {a['summary']}\n"
        news_string += "---\n"
    return news_string

def analyze_business_implications(articles: List[Dict]) -> str:
    """
    Sends the aggregated news to Groq LLM (Llama 3.3 70B)
    to extract actionable business implications.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("No GROQ_API_KEY found in environment. Using mock response.")
        return "⚠️ **Warning**: No `GROQ_API_KEY` provided. Please add it to your `.env` file."

    if Groq is None:
        logger.error("groq package not installed. Run: pip install groq")
        return "⚠️ **Error**: groq package not installed."

    client = Groq(api_key=api_key)

    prompt = f"""You are an expert financial and business strategy consultant.
I have fetched today's leading technology, financial, and business news articles.
Please read through the articles and provide a comprehensive, executive-summary level report outlining the core 'business implications' of these events.

For each major theme you identify in the news:
1. Explain what happened (briefly).
2. Explain the business and market implications (what this means for companies, investors, or the economy).
3. Provide a forward-looking prediction on what might happen next based on these events.

Here are the news articles:
{filter_recent_news(articles)}

Format your output in clean, readable Markdown using appropriate headings, bullet points, and bold text. Keep the tone professional, analytical, and actionable.
"""

    logger.info("Sending prompt to Groq API (Llama 3.3 70B)...")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return f"⚠️ **Error during AI Analysis**: {str(e)}"


if __name__ == "__main__":
    dummy_articles = [
        {
            "title": "Fed rate cuts signal new era for housing market",
            "source": "WSJ Business",
            "summary": "The Federal Reserve dropped rates by 50 basis points, stirring rapid mortgage refinance applications."
        },
        {
            "title": "AI boom fuels new multibillion dollar startup valuations",
            "source": "TechCrunch",
            "summary": "Several artificial intelligence startups have raised massive rounds as the generative AI race continues globally."
        }
    ]
    result = analyze_business_implications(dummy_articles)
    print("--- Analysis Result ---")
    print(result)
