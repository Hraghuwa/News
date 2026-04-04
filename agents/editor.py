import json
import logging
from typing import Any
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a world-class financial and business intelligence analyst. Your readers are investors, operators, and decision-makers who need structured, actionable analysis — not summaries.

Rules:
- Create ONE section per individual article — cover EVERY article provided, across ALL sectors (Technology, Business & Finance, India Finance, India Policy, Geopolitics, etc.)
- Use specific numbers, company names, policy names, and sector references. Never be vague.
- "industry_disruption" must be 3-5 concrete bullet points, not generic statements.
- "investment_angle" must name specific industries, asset classes, or companies that benefit or lose.
- "action_signal" must be a single specific move — not "monitor closely" or "watch this space".
- The "contrarian_spotlight" is the single most surprising non-consensus insight across ALL articles.

Return a single JSON object with this exact structure:
{
  "subject_line": "max 60 chars — punchy, specific, no clickbait",
  "preview_text": "max 90 chars — hooks the reader before they open",
  "opening_hook": "2-3 sentences that make the reader NEED to read further",
  "sections": [
    {
      "headline": "exact article title",
      "sector": "category name",
      "impact_score": 85,
      "is_black_swan": false,
      "memory_callback": "empty string, or e.g. 'This is the 3rd RBI rate hold this quarter' if historical context applies",
      "what_happened": "1-2 sentences — factual summary of the event. What exactly happened, who did it, what changed.",
      "industry_disruption": [
        "Bullet 1: specific industry or company that is disrupted and how",
        "Bullet 2: regulatory or competitive shift this triggers",
        "Bullet 3: who loses market share or faces new headwinds"
      ],
      "investment_angle": "Specific opportunities — name the sectors, asset classes, or companies that stand to gain. Be concrete.",
      "action_signal": "Single specific action: e.g. 'Accumulate IRFC bonds ahead of Q1 infra disbursals' or 'Short legacy media ETFs as AI content scales'"
    }
  ],
  "contrarian_spotlight": {
    "title": "What Everyone Is Missing",
    "body": "2-3 sentences — the single most surprising contrarian insight across all sectors",
    "source_sector": "which sector this came from"
  },
  "black_swan_alerts": [],
  "closing": "1-2 sentences — forward-looking, sets up what to watch tomorrow",
  "stats": {
    "articles_analyzed": 0,
    "high_impact_count": 0,
    "black_swans_flagged": 0,
    "avg_impact_score": 0.0,
    "sectors_covered": 0
  }
}"""


class EditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Editor", temperature=0.70)

    def compile(
        self,
        high_impact_articles: list[dict],
        expert_analyses: dict[str, Any],
        contrarian_insights: dict[str, Any],
        all_scored: list[dict],
        threshold: int = 80,
    ) -> dict[str, Any]:
        user_message = self._build_prompt(high_impact_articles, expert_analyses, contrarian_insights, all_scored, threshold)
        raw = self.call(SYSTEM_PROMPT, user_message, max_tokens=3500)
        result = self.parse_json(raw)

        if not result:
            logger.warning("Editor returned empty result. Building fallback newsletter.")
            result = self._fallback_newsletter(high_impact_articles, expert_analyses, contrarian_insights, all_scored)

        # Ensure stats are populated
        result.setdefault("stats", {})
        result["stats"]["articles_analyzed"] = len(all_scored)
        result["stats"]["high_impact_count"] = len(high_impact_articles)
        result["stats"]["black_swans_flagged"] = sum(1 for a in all_scored if a.get("is_black_swan"))
        result["stats"]["avg_impact_score"] = round(sum(a.get("score", 0) for a in all_scored) / max(len(all_scored), 1), 1)
        result["stats"]["sectors_covered"] = len(expert_analyses)

        # Extract black swan alerts from sections
        if not result.get("black_swan_alerts"):
            result["black_swan_alerts"] = [
                {"headline": s["headline"], "body": s.get("what_happened", ""), "score": s.get("impact_score", 95)}
                for s in result.get("sections", [])
                if s.get("is_black_swan")
            ]

        return result

    def _build_prompt(self, high_impact_articles, expert_analyses, contrarian_insights, all_scored, threshold):
        parts = ["Analyze EVERY article listed below. Produce one section per article covering all sectors.\n"]

        parts.append(f"=== ALL ARTICLES TO ANALYZE ({len(high_impact_articles)} total) ===")
        for a in high_impact_articles:
            flag = "🚨 BLACK SWAN" if a.get("is_black_swan") else ""
            parts.append(f"• [Score {a.get('score', '?')} | {a.get('category', '')}] [{a['source']}] {a['title']} {flag}")
            if a.get("summary"):
                parts.append(f"  Context: {a['summary'][:200]}")
            if a.get("reasoning"):
                parts.append(f"  Impact reasoning: {a['reasoning']}")
        parts.append("")

        parts.append("=== EXPERT ANALYSIS PER SECTOR ===")
        for sector, data in expert_analyses.items():
            if not isinstance(data, dict):
                continue
            parts.append(f"\n[{sector}]")
            parts.append(f"Summary: {data.get('summary', '')}")
            parts.append(f"Narrative: {data.get('emerging_narrative', '')}")
            lenses = data.get("lenses", {})
            for lens, text in lenses.items():
                if text:
                    parts.append(f"  {lens}: {text[:150]}")
        parts.append("")

        parts.append("=== CONTRARIAN INSIGHTS ===")
        for sector, c in contrarian_insights.items():
            if not isinstance(c, dict):
                continue
            parts.append(f"\n[{sector}]")
            parts.append(f"Blind spot: {c.get('blind_spot', '')}")
            parts.append(f"Opportunity: {c.get('hidden_opportunity', '')}")
            parts.append(f"One-liner: {c.get('one_liner', '')}")
        parts.append("")

        black_swans = [a for a in all_scored if a.get("is_black_swan")]
        if black_swans:
            parts.append("=== 🚨 BLACK SWAN ALERTS ===")
            for a in black_swans:
                parts.append(f"• Score {a.get('score')} — {a['title']}")

        return "\n".join(parts)

    def _fallback_newsletter(self, high_impact_articles, expert_analyses, contrarian_insights, all_scored):
        sections = []
        for article in high_impact_articles[:20]:
            sector = article.get("category", "General")
            data = expert_analyses.get(sector, {})
            c = contrarian_insights.get(sector, {})
            sections.append({
                "headline": article.get("title", ""),
                "sector": sector,
                "impact_score": article.get("score", 80),
                "is_black_swan": article.get("is_black_swan", False),
                "memory_callback": "",
                "what_happened": article.get("summary", "")[:250],
                "industry_disruption": [
                    data.get("emerging_narrative", "Market impact under analysis."),
                    c.get("blind_spot", "Competitive dynamics shifting."),
                ],
                "investment_angle": c.get("hidden_opportunity", "Opportunities under analysis."),
                "action_signal": c.get("contrarian_bet", "Review exposure to this sector."),
            })

        best_contrarian = next(
            ({"title": "What Everyone Is Missing", "body": c.get("blind_spot", "") + " " + c.get("hidden_opportunity", ""), "source_sector": s}
             for s, c in contrarian_insights.items() if isinstance(c, dict) and c.get("blind_spot")),
            {"title": "What Everyone Is Missing", "body": "No contrarian view available.", "source_sector": ""}
        )

        return {
            "subject_line": "Daily Intelligence Report",
            "preview_text": "Your daily strategic briefing.",
            "opening_hook": "Today's top stories analyzed across finance, tech, geopolitics, and India policy.",
            "sections": sections,
            "contrarian_spotlight": best_contrarian,
            "black_swan_alerts": [],
            "closing": "Watch these stories closely tomorrow.",
            "stats": {},
        }
