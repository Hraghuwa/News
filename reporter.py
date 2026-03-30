import os
import re
import datetime
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def markdown_to_html(text: str) -> str:
    """Convert basic markdown to HTML for email rendering."""
    # Bold **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic *text*
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # H3 headers
    text = re.sub(r'^### (.+)$', r'<h3 style="color:#1a73e8;margin:16px 0 6px;">\1</h3>', text, flags=re.MULTILINE)
    # H2 headers
    text = re.sub(r'^## (.+)$', r'<h2 style="color:#0d47a1;border-bottom:2px solid #e8f0fe;padding-bottom:8px;margin-top:24px;">\1</h2>', text, flags=re.MULTILINE)
    # H1 headers
    text = re.sub(r'^# (.+)$', r'<h1 style="color:#0d47a1;">\1</h1>', text, flags=re.MULTILINE)
    # Bullet points
    text = re.sub(r'^\s*[-•] (.+)$', r'<li style="margin:4px 0;">\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li.*?</li>\n?)+', r'<ul style="padding-left:20px;margin:8px 0;">\g<0></ul>', text)
    # Numbered lists
    text = re.sub(r'^\d+\. (.+)$', r'<li style="margin:4px 0;">\1</li>', text, flags=re.MULTILINE)
    # Horizontal rules
    text = text.replace('---', '<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">')
    # Paragraphs (double newlines)
    paragraphs = text.split('\n\n')
    result = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p style="margin:8px 0;line-height:1.7;color:#333;">{p.replace(chr(10), "<br>")}</p>'
        result.append(p)
    return '\n'.join(result)


def build_html_email(date_str: str, analysis_text: str, articles: list) -> str:
    """Build a beautiful HTML email."""

    day_name = datetime.date.today().strftime("%A, %B %d, %Y")
    analysis_html = markdown_to_html(analysis_text)

    # Build article cards
    article_cards = ""
    source_colors = {
        "TechCrunch": "#0f9d58",
        "CNBC Top News": "#1a73e8",
        "WSJ Business": "#c62828",
        "Wired Tech": "#6200ea",
    }
    for i, a in enumerate(articles, 1):
        color = source_colors.get(a['source'], "#455a64")
        article_cards += f"""
        <div style="background:#fff;border:1px solid #e8eaf6;border-radius:10px;padding:18px 20px;margin-bottom:14px;border-left:4px solid {color};">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="background:{color};color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px;letter-spacing:0.5px;">{a['source']}</span>
                <span style="color:#9e9e9e;font-size:12px;">#{i}</span>
            </div>
            <h3 style="margin:0 0 8px;font-size:15px;color:#1a1a1a;line-height:1.4;">{a['title']}</h3>
            <p style="margin:0;color:#555;font-size:13px;line-height:1.6;">{a['summary'][:300]}{'...' if len(a['summary']) > 300 else ''}</p>
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily News Report</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">

  <!-- Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:30px 10px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#0d47a1 0%,#1565c0 50%,#1976d2 100%);border-radius:14px 14px 0 0;padding:36px 40px 28px;text-align:center;">
          <div style="font-size:32px;margin-bottom:6px;">📊</div>
          <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:700;letter-spacing:-0.3px;">Daily Strategic Report</h1>
          <p style="margin:8px 0 0;color:#bbdefb;font-size:14px;">{day_name}</p>
        </td></tr>

        <!-- Stats Bar -->
        <tr><td style="background:#1565c0;padding:14px 40px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td align="center" style="color:#e3f2fd;font-size:13px;">
                <strong style="font-size:20px;color:#fff;display:block;">{len(articles)}</strong>
                Articles Fetched
              </td>
              <td align="center" style="color:#e3f2fd;font-size:13px;border-left:1px solid #1976d2;border-right:1px solid #1976d2;">
                <strong style="font-size:20px;color:#fff;display:block;">3</strong>
                Sources Monitored
              </td>
              <td align="center" style="color:#e3f2fd;font-size:13px;">
                <strong style="font-size:20px;color:#fff;display:block;">AI</strong>
                Powered by Llama 3.3
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Body -->
        <tr><td style="background:#ffffff;padding:36px 40px;">

          <!-- AI Analysis Section -->
          <div style="background:#f8f9ff;border:1px solid #c5cae9;border-radius:10px;padding:24px;margin-bottom:32px;">
            <h2 style="margin:0 0 16px;color:#283593;font-size:18px;display:flex;align-items:center;gap:8px;">
              🤖 AI Executive Analysis
            </h2>
            <div style="font-size:14px;line-height:1.8;color:#333;">
              {analysis_html}
            </div>
          </div>

          <!-- Headlines Section -->
          <h2 style="margin:0 0 20px;color:#283593;font-size:18px;border-bottom:2px solid #e8eaf6;padding-bottom:10px;">
            📰 Today's Top Headlines
          </h2>
          {article_cards}

        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#263238;border-radius:0 0 14px 14px;padding:24px 40px;text-align:center;">
          <p style="margin:0 0 6px;color:#90a4ae;font-size:12px;">
            🤖 Automated Daily News Agent &nbsp;|&nbsp; Powered by Groq + Llama 3.3 70B
          </p>
          <p style="margin:0;color:#546e7a;font-size:11px;">
            Delivered every morning at 9:00 AM IST &nbsp;•&nbsp; {date_str}
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>

</body>
</html>
"""
    return html


def generate_markdown_report(analysis_text: str, articles: list = None):
    """Saves the analysis as a markdown file and sends a beautiful HTML email."""
    ensure_reports_dir()

    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"Business_Implications_Report_{date_str}.md"
    file_path = os.path.join(REPORTS_DIR, filename)

    # Save plain markdown file
    report_content = f"# Daily Strategic Business & Tech Report\n*Date: {date_str}*\n\n"
    report_content += "## 🤖 AI Executive Analysis\n\n" + analysis_text + "\n\n---\n\n"
    if articles:
        report_content += "## 📰 Today's Top Headlines\n\n"
        for i, a in enumerate(articles, 1):
            report_content += f"### {i}. {a['title']}\n**Source:** {a['source']}\n\n{a['summary']}\n\n---\n\n"
    report_content += "*Report dynamically generated by Daily News Analyzer Agent.*"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Successfully generated report at: {file_path}")

    send_slack_notification(report_content)
    send_email_notification(date_str, analysis_text, articles or [])

    return file_path


def send_slack_notification(content: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.debug("Slack Webhook URL not configured. Skipping.")
        return
    try:
        payload = {"text": f"*Daily Business Report*\n\n{content}"[:3500]}
        requests.post(webhook_url, json=payload).raise_for_status()
        logger.info("Successfully sent Slack notification.")
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")


def send_email_notification(date_str: str, analysis_text: str, articles: list):
    sender   = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")
    smtp_server = os.getenv("SMTP_SERVER") or "smtp.gmail.com"
    try:
        smtp_port = int(os.getenv("SMTP_PORT") or "587")
    except ValueError:
        smtp_port = 587

    if not all([sender, password, receiver]):
        logger.debug("Email credentials not fully configured. Skipping.")
        return

    logger.info(f"Sending Email report to {receiver}...")
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"Daily News Agent <{sender}>"
        msg["To"]      = receiver
        msg["Subject"] = f"📊 Daily Strategic Report — {datetime.date.today().strftime('%B %d, %Y')}"

        # Plain text fallback
        plain = f"Daily Strategic Report - {date_str}\n\nAI Analysis:\n{analysis_text}\n\nTop Headlines:\n"
        for i, a in enumerate(articles, 1):
            plain += f"\n{i}. {a['title']} ({a['source']})\n{a['summary']}\n"
        msg.attach(MIMEText(plain, "plain"))

        # Beautiful HTML version
        html = build_html_email(date_str, analysis_text, articles)
        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

        logger.info("Successfully sent Email notification.")
    except Exception as e:
        logger.error(f"Failed to send Email notification: {e}")


if __name__ == "__main__":
    generate_markdown_report("Mock analysis data from the test run.", [
        {"title": "Test headline", "source": "TechCrunch", "summary": "This is a test summary."}
    ])
