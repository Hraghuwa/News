import os
import datetime
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from fetcher import CATEGORY_COLORS

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


# ── Score badge helper ────────────────────────────────────────────────────────

def _score_badge(score: int) -> str:
    if score >= 95:
        color, label = "#c62828", f"🚨 {score}"
    elif score >= 80:
        color, label = "#e65100", str(score)
    else:
        color, label = "#546e7a", str(score)
    return (
        f'<span style="background:{color};color:#fff;font-size:11px;font-weight:700;'
        f'padding:2px 7px;border-radius:20px;letter-spacing:0.3px;">{label}</span>'
    )


# ── Section: Black Swan Alerts ────────────────────────────────────────────────

def _build_black_swan_section(alerts: list[dict]) -> str:
    if not alerts:
        return ""
    rows = ""
    for a in alerts:
        rows += f"""
        <div style="border-top:1px solid #4a0000;padding:12px 0;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            {_score_badge(a.get('score', 95))}
            <strong style="color:#ef9a9a;font-size:14px;">{a.get('headline','')}</strong>
          </div>
          <p style="margin:0;color:#ffcdd2;font-size:13px;line-height:1.6;">{a.get('body','')}</p>
        </div>"""
    return f"""
    <div style="background:linear-gradient(135deg,#1a0000,#3b0000);
                border:2px solid #ef5350;border-radius:12px;
                padding:20px 24px;margin-bottom:28px;">
      <h2 style="color:#ef5350;margin:0 0 4px;font-size:13px;font-weight:800;
                 letter-spacing:2px;text-transform:uppercase;">
        🚨 BLACK SWAN ALERT — RARE MARKET-SHIFTING EVENT DETECTED
      </h2>
      {rows}
    </div>"""


# ── Section: Opening Hook ─────────────────────────────────────────────────────

def _build_opening_hook(hook: str) -> str:
    if not hook:
        return ""
    return f"""
    <div style="background:#e8f5e9;border-left:4px solid #2e7d32;border-radius:6px;
                padding:18px 22px;margin-bottom:28px;">
      <p style="margin:0;color:#1b5e20;font-size:15px;line-height:1.75;font-style:italic;">
        {hook}
      </p>
    </div>"""


# ── Section: Structured Analysis Cards (per article) ─────────────────────────

def _build_expert_sections(sections: list[dict]) -> str:
    if not sections:
        return ""
    cards = ""
    for s in sections:
        sector = s.get("sector", "")
        color = CATEGORY_COLORS.get(sector, "#455a64")
        score = s.get("impact_score", 0)

        bs_flag = ""
        if s.get("is_black_swan"):
            bs_flag = ' <span style="background:#c62828;color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">🚨 BLACK SWAN</span>'

        memory_cb = s.get("memory_callback", "")
        memory_html = f'<p style="margin:0 0 10px;color:#78909c;font-size:11px;font-style:italic;">🕐 {memory_cb}</p>' if memory_cb else ""

        # What Happened
        what_happened = s.get("what_happened", "")
        what_happened_html = f"""
          <div style="margin-bottom:12px;">
            <span style="color:#37474f;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;display:block;margin-bottom:4px;">What Happened</span>
            <p style="margin:0;color:#333;font-size:13px;line-height:1.7;">{what_happened}</p>
          </div>""" if what_happened else ""

        # Industry Disruption bullets
        disruptions = s.get("industry_disruption", [])
        if isinstance(disruptions, list) and disruptions:
            bullet_items = "".join(
                f'<li style="margin:4px 0;color:#444;font-size:13px;line-height:1.6;">{d}</li>'
                for d in disruptions if d
            )
            disruption_html = f"""
          <div style="margin-bottom:12px;">
            <span style="color:#37474f;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;display:block;margin-bottom:6px;">Industry Disruption</span>
            <ul style="margin:0;padding-left:18px;">{bullet_items}</ul>
          </div>"""
        else:
            disruption_html = ""

        # Investment Angle
        investment = s.get("investment_angle", "")
        investment_html = f"""
          <div style="background:#e8f5e9;border-radius:6px;padding:10px 14px;margin-bottom:10px;">
            <span style="color:#1b5e20;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;display:block;margin-bottom:3px;">Investment Angle</span>
            <p style="margin:0;color:#1b5e20;font-size:13px;line-height:1.6;">{investment}</p>
          </div>""" if investment else ""

        # Action Signal
        action = s.get("action_signal", "")
        action_html = f"""
          <div style="background:#e3f2fd;border-radius:6px;padding:10px 14px;">
            <span style="color:#0d47a1;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;display:block;margin-bottom:3px;">Action Signal</span>
            <p style="margin:0;color:#0d47a1;font-size:13px;font-weight:600;line-height:1.6;">{action}</p>
          </div>""" if action else ""

        cards += f"""
        <div style="background:#fff;border:1px solid #e8eaf6;border-radius:12px;
                    padding:20px 22px;margin-bottom:18px;border-left:5px solid {color};">
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:12px;">
            <span style="background:{color};color:#fff;font-size:11px;font-weight:700;
                         padding:3px 10px;border-radius:20px;">{sector}</span>
            {_score_badge(score)}
            {bs_flag}
          </div>
          <h3 style="margin:0 0 12px;font-size:15px;color:#1a1a1a;line-height:1.4;font-weight:700;">
            {s.get('headline','')}
          </h3>
          {memory_html}
          {what_happened_html}
          {disruption_html}
          {investment_html}
          {action_html}
        </div>"""

    return f"""
    <h2 style="margin:0 0 20px;color:#283593;font-size:18px;border-bottom:2px solid #e8eaf6;padding-bottom:10px;">
      🧠 Full Intelligence Analysis — Every Story, Every Sector
    </h2>
    {cards}"""


# ── Section: Contrarian Spotlight ────────────────────────────────────────────

def _build_contrarian_spotlight(spotlight: dict) -> str:
    if not spotlight or not spotlight.get("body"):
        return ""
    sector = spotlight.get("source_sector", "")
    return f"""
    <div style="background:linear-gradient(135deg,#0d1321,#1a1030);
                border-left:4px solid #ce93d8;border-radius:10px;
                padding:22px 26px;margin-bottom:28px;">
      <h3 style="color:#ce93d8;margin:0 0 10px;font-size:13px;font-weight:800;
                 letter-spacing:2px;text-transform:uppercase;">
        🔍 What Everyone Is Missing
      </h3>
      <p style="margin:0 0 12px;color:#e0d7f5;font-size:14px;line-height:1.8;">
        {spotlight.get('body','')}
      </p>
      {'<span style="color:#7986cb;font-size:11px;">Source sector: ' + sector + '</span>' if sector else ''}
    </div>"""


# ── Section: Impact Score Leaderboard ────────────────────────────────────────

def _build_leaderboard(all_scored: list[dict]) -> str:
    if not all_scored:
        return ""
    top15 = sorted(all_scored, key=lambda x: x.get("score", 0), reverse=True)[:15]
    rows = ""
    for a in top15:
        score = a.get("score", 0)
        source_color = CATEGORY_COLORS.get(a.get("category", ""), "#455a64")
        rows += f"""
        <tr style="border-bottom:1px solid #1e2736;">
          <td style="padding:8px 4px;width:60px;">{_score_badge(score)}</td>
          <td style="padding:8px;color:#cfd8dc;font-size:13px;line-height:1.4;">{a.get('title','')[:80]}{'...' if len(a.get('title','')) > 80 else ''}</td>
          <td style="padding:8px 4px;white-space:nowrap;">
            <span style="background:{source_color};color:#fff;font-size:10px;font-weight:700;
                         padding:2px 7px;border-radius:20px;">{a.get('source','')[:18]}</span>
          </td>
        </tr>"""
    return f"""
    <div style="background:#0a1020;border:1px solid #1e2736;border-radius:12px;
                padding:20px 24px;margin-bottom:28px;">
      <h2 style="color:#ffd600;margin:0 0 16px;font-size:15px;font-weight:800;
                 letter-spacing:1px;">
        📊 Impact Score Leaderboard — Top Stories Today
      </h2>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <th style="color:#546e7a;font-size:11px;text-align:left;padding:0 4px 8px;">SCORE</th>
          <th style="color:#546e7a;font-size:11px;text-align:left;padding:0 8px 8px;">HEADLINE</th>
          <th style="color:#546e7a;font-size:11px;text-align:left;padding:0 4px 8px;">SOURCE</th>
        </tr>
        {rows}
      </table>
    </div>"""


# ── Section: Raw Article Cards (all headlines, lightweight) ──────────────────

def _build_article_cards(articles: list[dict], newsletter_sections: list[dict] = None) -> str:
    # Build set of headlines already covered in full analysis
    analyzed_titles: set[str] = {s.get("headline", "").lower().strip() for s in (newsletter_sections or [])}

    cards = ""
    count = 0
    for a in articles:
        title = a.get("title", "")
        if title.lower().strip() in analyzed_titles:
            continue  # Skip — already shown with full analysis above
        count += 1
        if count > 15:
            break
        category = a.get("category", "")
        color = CATEGORY_COLORS.get(category, "#455a64")
        summary = a.get("summary", "")
        score = a.get("score")
        score_html = f" {_score_badge(score)}" if score else ""

        cards += f"""
        <div style="background:#fafafa;border:1px solid #e8eaf6;border-radius:8px;
                    padding:14px 16px;margin-bottom:10px;border-left:3px solid {color};">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
            <span style="background:{color};color:#fff;font-size:10px;font-weight:700;
                         padding:2px 8px;border-radius:20px;">{a.get('source','')}</span>
            {score_html}
          </div>
          <p style="margin:0 0 4px;color:#1a1a1a;font-size:13px;font-weight:600;line-height:1.4;">{title}</p>
          <p style="margin:0;color:#777;font-size:12px;line-height:1.5;">{summary[:220]}{'...' if len(summary) > 220 else ''}</p>
        </div>"""

    if not cards:
        return ""
    return f"""
    <h2 style="margin:28px 0 14px;color:#546e7a;font-size:15px;border-bottom:1px solid #e8eaf6;padding-bottom:8px;">
      📰 Additional Headlines
    </h2>
    {cards}"""


# ── Main HTML builder ─────────────────────────────────────────────────────────

def build_html_email(date_str: str, newsletter: dict, articles: list[dict], all_scored: list[dict]) -> str:
    day_name = datetime.date.today().strftime("%A, %B %d, %Y")
    stats = newsletter.get("stats", {})

    total = stats.get("articles_analyzed", len(all_scored))
    high_impact = stats.get("high_impact_count", 0)
    black_swans = stats.get("black_swans_flagged", 0)
    avg_score = stats.get("avg_impact_score", 0.0)
    sectors = stats.get("sectors_covered", 0)

    subject = newsletter.get("subject_line", "Daily Intelligence Report")
    closing = newsletter.get("closing", "")

    black_swan_html = _build_black_swan_section(newsletter.get("black_swan_alerts", []))
    hook_html = _build_opening_hook(newsletter.get("opening_hook", ""))
    expert_html = _build_expert_sections(newsletter.get("sections", []))
    contrarian_html = _build_contrarian_spotlight(newsletter.get("contrarian_spotlight", {}))
    leaderboard_html = _build_leaderboard(all_scored)
    article_cards_html = _build_article_cards(articles, newsletter.get("sections", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:30px 10px;">
    <tr><td align="center">
      <table width="660" cellpadding="0" cellspacing="0" style="max-width:660px;width:100%;">

        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#0d47a1 0%,#1565c0 50%,#1976d2 100%);
                        border-radius:14px 14px 0 0;padding:36px 40px 28px;text-align:center;">
          <div style="font-size:32px;margin-bottom:6px;">🧠</div>
          <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;letter-spacing:-0.3px;">
            Daily Intelligence Report
          </h1>
          <p style="margin:8px 0 4px;color:#bbdefb;font-size:14px;">{day_name}</p>
          <p style="margin:0;color:#90caf9;font-size:13px;font-style:italic;">{subject}</p>
        </td></tr>

        <!-- Stats Bar -->
        <tr><td style="background:#1565c0;padding:14px 40px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td align="center" style="color:#e3f2fd;font-size:12px;">
                <strong style="font-size:19px;color:#fff;display:block;">{total}</strong>
                Articles Scored
              </td>
              <td align="center" style="color:#e3f2fd;font-size:12px;border-left:1px solid #1976d2;">
                <strong style="font-size:19px;color:#fff;display:block;">{high_impact}</strong>
                High-Impact (80+)
              </td>
              <td align="center" style="color:#e3f2fd;font-size:12px;border-left:1px solid #1976d2;">
                <strong style="font-size:19px;color:{'#ef5350' if black_swans else '#fff'};display:block;">{black_swans}</strong>
                Black Swans 🚨
              </td>
              <td align="center" style="color:#e3f2fd;font-size:12px;border-left:1px solid #1976d2;">
                <strong style="font-size:19px;color:#fff;display:block;">{avg_score}</strong>
                Avg Score
              </td>
              <td align="center" style="color:#e3f2fd;font-size:12px;border-left:1px solid #1976d2;">
                <strong style="font-size:19px;color:#fff;display:block;">{sectors}</strong>
                Sectors
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Body -->
        <tr><td style="background:#ffffff;padding:36px 40px;">

          {black_swan_html}
          {hook_html}
          {expert_html}
          {contrarian_html}
          {leaderboard_html}

          <!-- Raw Headlines -->
          <h2 style="margin:0 0 16px;color:#283593;font-size:18px;border-bottom:2px solid #e8eaf6;padding-bottom:10px;">
            📰 All Today's Headlines
          </h2>
          {article_cards_html}

          <!-- Closing -->
          {'<div style="background:#f8f9ff;border-radius:8px;padding:16px 20px;margin-top:24px;"><p style="margin:0;color:#3949ab;font-size:14px;line-height:1.7;font-style:italic;">' + closing + '</p></div>' if closing else ''}

        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#263238;border-radius:0 0 14px 14px;padding:24px 40px;text-align:center;">
          <p style="margin:0 0 6px;color:#90a4ae;font-size:12px;">
            🤖 4-Agent Intelligence System &nbsp;|&nbsp; Powered by Groq + Llama 3.3 70B
          </p>
          <p style="margin:0;color:#546e7a;font-size:11px;">
            Delivered every morning at 9:00 AM IST &nbsp;•&nbsp; {date_str}
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>

</body>
</html>"""


# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(newsletter: dict, articles: list[dict], all_scored: list[dict]) -> str:
    ensure_reports_dir()
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    file_path = os.path.join(REPORTS_DIR, f"Intelligence_Report_{date_str}.md")

    sections_md = ""
    for s in newsletter.get("sections", []):
        sections_md += f"### {s.get('headline','')}\n**Sector:** {s.get('sector','')} | **Score:** {s.get('impact_score','')}\n\n{s.get('body','')}\n\n**Key Insight:** {s.get('key_insight','')}\n\n**Action Signal:** {s.get('action_signal','')}\n\n---\n\n"

    spotlight = newsletter.get("contrarian_spotlight", {})
    contrarian_md = f"## 🔍 Contrarian Spotlight\n\n{spotlight.get('body','')}\n\n" if spotlight.get("body") else ""

    report_content = f"""# Daily Intelligence Report — {date_str}

*{newsletter.get('subject_line','')}*

## Opening

{newsletter.get('opening_hook','')}

## Expert Analysis

{sections_md}

{contrarian_md}

## Closing

{newsletter.get('closing','')}

---
*Generated by 4-Agent Intelligence Pipeline — Groq + Llama 3.3 70B*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    logger.info(f"Report saved to {file_path}")

    send_slack_notification(report_content)
    send_email_notification(date_str, newsletter, articles, all_scored)

    return file_path


def send_slack_notification(content: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.debug("Slack Webhook not configured. Skipping.")
        return
    try:
        payload = {"text": f"*Daily Intelligence Report*\n\n{content}"[:3500]}
        requests.post(webhook_url, json=payload).raise_for_status()
        logger.info("Slack notification sent.")
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")


def send_email_notification(date_str: str, newsletter: dict, articles: list[dict], all_scored: list[dict]):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")
    smtp_server = os.getenv("SMTP_SERVER") or "smtp.gmail.com"
    try:
        smtp_port = int(os.getenv("SMTP_PORT") or "587")
    except ValueError:
        smtp_port = 587

    if not all([sender, password, receiver]):
        missing = [k for k, v in {"EMAIL_SENDER": sender, "EMAIL_PASSWORD": password, "EMAIL_RECEIVER": receiver}.items() if not v]
        logger.warning(f"Email skipped — missing secrets: {missing}")
        return

    subject_line = newsletter.get("subject_line", f"Daily Intelligence Report — {date_str}")
    logger.info(f"Sending email to {receiver}...")
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Intelligence Agent <{sender}>"
        msg["To"] = receiver
        msg["Subject"] = f"🧠 {subject_line} — {datetime.date.today().strftime('%B %d, %Y')}"

        # Plain text fallback
        plain = f"Daily Intelligence Report — {date_str}\n\n"
        plain += f"{newsletter.get('opening_hook','')}\n\n"
        for s in newsletter.get("sections", []):
            plain += f"[{s.get('sector','')} | Score {s.get('impact_score','')}] {s.get('headline','')}\n{s.get('body','')}\n\n"
        msg.attach(MIMEText(plain, "plain"))

        # HTML version
        html = build_html_email(date_str, newsletter, articles, all_scored)
        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Email failed: {e}")
