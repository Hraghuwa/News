import datetime
import logging

from fetcher import fetch_daily_news
from scoring import ImpactScorer
from memory import RAGMemory
from agents import SectorExpertAgent, ContrarianAgent, EditorAgent
from reporter import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    logger.info("=" * 60)
    logger.info("   DAILY INTELLIGENCE PIPELINE STARTING")
    logger.info("=" * 60)

    # ── Step 1: Fetch ────────────────────────────────────────────
    logger.info("Step 1/7 — Fetching news from RSS feeds...")
    articles = fetch_daily_news(max_articles_per_feed=4)
    if not articles:
        logger.error("No articles fetched. Aborting pipeline.")
        return
    logger.info(f"  → {len(articles)} articles fetched across {len(set(a['category'] for a in articles))} categories.")

    # ── Step 2: Impact Scoring ───────────────────────────────────
    logger.info("Step 2/7 — Scoring articles for impact (1-100)...")
    scorer = ImpactScorer()
    high_impact, all_scored = scorer.score_all(articles)

    if not high_impact:
        logger.warning("No articles scored ≥80. Using top 10 by score as fallback.")
        high_impact = sorted(all_scored, key=lambda x: x.get("score", 0), reverse=True)[:10]

    black_swans = [a for a in all_scored if a.get("is_black_swan")]
    logger.info(f"  → {len(high_impact)} high-impact articles | {len(black_swans)} black swans detected.")

    # ── Step 3: Memory Retrieval ─────────────────────────────────
    logger.info("Step 3/7 — Retrieving historical context from memory...")
    memory = RAGMemory()
    query = " ".join(a["title"] for a in high_impact[:10])
    memory_context = memory.retrieve_context(query)
    if memory_context:
        logger.info(f"  → Historical context found ({len(memory_context)} chars).")
    else:
        logger.info("  → No relevant historical context (cold start or no match).")

    # Group high-impact articles by category
    articles_by_category: dict[str, list[dict]] = {}
    for a in high_impact:
        articles_by_category.setdefault(a["category"], []).append(a)

    # ── Step 4: Sector Expert Analysis ──────────────────────────
    logger.info(f"Step 4/7 — Running Sector Expert analysis across {len(articles_by_category)} categories...")
    expert = SectorExpertAgent()
    expert_analyses = expert.analyze(articles_by_category, memory_context)
    logger.info(f"  → Expert analysis complete for {len(expert_analyses)} sectors.")

    # ── Step 5: Contrarian Debate ────────────────────────────────
    logger.info("Step 5/7 — Running Contrarian agent (finding what the market misses)...")
    contrarian = ContrarianAgent()
    contrarian_insights = contrarian.debate(expert_analyses)
    logger.info(f"  → Contrarian insights generated for {len(contrarian_insights)} sectors.")

    # ── Step 6: Editor Compilation ───────────────────────────────
    logger.info("Step 6/7 — Editor compiling final newsletter...")
    editor = EditorAgent()
    newsletter = editor.compile(
        high_impact_articles=high_impact,
        expert_analyses=expert_analyses,
        contrarian_insights=contrarian_insights,
        all_scored=all_scored,
    )
    logger.info(f"  → Newsletter compiled: {len(newsletter.get('sections', []))} sections, subject: \"{newsletter.get('subject_line', '')}\"")

    # ── Step 7: Save Memory ──────────────────────────────────────
    logger.info("Step 7/7 — Saving run to memory...")
    memory.append_run(
        date=datetime.date.today().isoformat(),
        sector_expert_output=expert_analyses,
        contrarian_output=contrarian_insights,
        impact_scores=all_scored,
    )

    # ── Report + Email ───────────────────────────────────────────
    logger.info("Generating report and sending email...")
    generate_report(newsletter, articles, all_scored)

    stats = newsletter.get("stats", {})
    logger.info("=" * 60)
    logger.info("   PIPELINE COMPLETE")
    logger.info(f"   Articles analyzed : {stats.get('articles_analyzed', len(all_scored))}")
    logger.info(f"   High-impact (80+) : {stats.get('high_impact_count', len(high_impact))}")
    logger.info(f"   Black swans (95+) : {stats.get('black_swans_flagged', len(black_swans))}")
    logger.info(f"   Avg impact score  : {stats.get('avg_impact_score', 'N/A')}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
