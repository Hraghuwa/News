import json
import logging
from typing import Any
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a world-class financial newsletter editor. Your 50,000 daily readers are time-poor, sophisticated, and allergic to fluff.

Rules:
- Create ONE section per individual article (not per sector).
- Each section must give the reader exactly 4 things: what happened, what to DO, what the crowd is MISSING, and what happens NEXT.
- Use specific numbers, company names, and policy references. No vague statements.
- The "contrarian_spotlight" is the single most memorable insight across all articles.

Return a single JSON object with this exact structure:
{
  "subject_line": "max 60 chars — punchy, specific, no clickbait",
  "preview_text": "max 90 chars — hooks the reader before they open",
  "opening_hook": "2-3 sentences that make the reader NEED to read further",
  "sections": [
    {
      "headline": "exact article title",
      "sector": "category name",
      "body": "2-3 sentences of analysis — what this means and why it matters",
      "impact_score": 85,
      "is_black_swan": false,
      "memory_callback": "empty string, or e.g. 'This is the 3rd RBI rate hold this quarter' if historical context applies",
      "action_signal": "specific action a smart investor/operator takes RIGHT NOW — be concrete",
      "what_everyone_is_missing": "the contrarian blind spot most readers will miss about THIS specific article",
      "future_perspective": "what happens in 3-6 months if this story plays out — name the likely winners and losers"
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
                {"headline": s["headline"], "body": s["body"], "score": s.get("impact_score", 95)}
                for s in result.get("sections", [])
                if s.get("is_black_swan")
            ]

        return result

    def _build_prompt(self, high_impact_articles, expert_analyses, contrarian_insights, all_scored, threshold):
        parts = [f"Compile a newsletter from the following intelligence. Only include stories scoring {threshold}+.\n"]

        parts.append(f"=== HIGH-IMPACT STORIES (score {threshold}+) ===")
        for a in high_impact_articles[:20]:
            flag = "🚨 BLACK SWAN" if a.get("is_black_swan") else ""
            parts.append(f"• [{a.get('score', '?')}] {a['title']} ({a['source']}) {flag}")
            if a.get("reasoning"):
                parts.append(f"  Reasoning: {a['reasoning']}")
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
        for article in high_impact_articles[:15]:
            sector = article.get("category", "General")
            data = expert_analyses.get(sector, {})
            c = contrarian_insights.get(sector, {})
            sections.append({
                "headline": article.get("title", ""),
                "sector": sector,
                "body": data.get("summary", article.get("summary", ""))[:300],
                "impact_score": article.get("score", 80),
                "is_black_swan": article.get("is_black_swan", False),
                "memory_callback": "",
                "action_signal": c.get("contrarian_bet", "Monitor this story closely."),
                "what_everyone_is_missing": c.get("blind_spot", "Analysis unavailable."),
                "future_perspective": data.get("emerging_narrative", "Watch for follow-on developments."),
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
