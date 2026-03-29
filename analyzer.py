import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Try to use the standard genai library
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
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
    Sends the aggregated news to the Gemini LLM endpoint
    to extract actionable business implications.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "paste_your_gemini_api_key_here":
        # Fallback if the user hasn't set up the API key yet
        logger.warning("No valid GEMINI_API_KEY found in environment. Using a mock response for demonstration.")
        return "⚠️ **Warning**: No `GEMINI_API_KEY` provided. \n\nPlease provide your API key in the `.env` file to enable AI-powered analysis. \n\n*Mock Output: Technology stocks expected to see turbulence, and new fintech regulations might impact upcoming quarters.*"

    if genai is None:
        logger.error("google-genai package not found or failed to load. Please properly install the `google-genai` package.")
        return "⚠️ **Error**: Failed to load the `google-genai` python package. AI analysis aborted."

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are an expert financial and business strategy consultant. 
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
    
    logger.info("Sending prompt to Gemini API...")
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return f"⚠️ **Error during AI Analysis**: {str(e)}"

if __name__ == "__main__":
    # Test analyzer with dummy data
    dummy_articles = [
        {
            "title": "Fed rate cuts signal new era for housing market",
            "source": "WSJ Business",
            "summary": "The Federal Reserve dropped rates by 50 basis points, stirring rapid mortgage refinance applications."
        },
        {
            "title": "AI boom fuels new multibillion dollar startup valuations",
            "source": "TechCrunch",
            "summary": "Several artificial intelligence startups have raised massive rounds as the generative AI race continues to heat up globally."
        }
    ]
    result = analyze_business_implications(dummy_articles)
    print("--- Analysis Result ---")
    print(result)
