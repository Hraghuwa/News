import logging
from typing import Any
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a multi-domain expert analyst with deep expertise in:
- Tech VC investing (startup ecosystems, AI infrastructure, disruption patterns)
- Geopolitical risk (alliance shifts, sanctions, trade wars, resource competition)
- Financial markets (macro signals, sector rotation, equity/bond/FX implications)
- India Government Policy (RBI, SEBI, PLI schemes, budget allocations, PSU dynamics, infrastructure projects)

You will receive news articles grouped by category. For each category, deliver structured expert analysis.

Return a single JSON object where each key is the category name and the value follows this exact schema:
{
  "summary": "2-3 sentence executive summary of what is really happening",
  "lenses": {
    "tech_vc": "What a VC sees — disruption, funding, winners/losers",
    "geopolitics": "Power dynamics, alliance shifts, sanctions angle",
    "financial_markets": "Sector impact, commodity/FX/bond signal, equity implication",
    "india_policy": "India-specific implication — RBI, SEBI, ministry, FDI, infra project"
  },
  "implications": [
    {"point": "specific implication", "timeframe": "short|medium|long", "confidence": "high|medium|low"}
  ],
  "emerging_narrative": "What multi-article pattern is forming across this category",
  "affected_sectors": ["Finance", "Energy", "Tech"]
}"""


class SectorExpertAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="SectorExpert", temperature=0.65)

    def analyze(self, articles_by_category: dict[str, list[dict]], memory_context: str = "") -> dict[str, Any]:
        user_message = self._build_prompt(articles_by_category, memory_context)
        raw = self.call(SYSTEM_PROMPT, user_message, max_tokens=3500)
        result = self.parse_json(raw)
        if not result:
            logger.warning("SectorExpert returned empty analysis. Using fallback.")
            result = {cat: {"summary": "Analysis unavailable.", "lenses": {}, "implications": [], "emerging_narrative": "", "affected_sectors": []} for cat in articles_by_category}
        return result

    def _build_prompt(self, articles_by_category: dict[str, list[dict]], memory_context: str) -> str:
        parts = []
        if memory_context:
            parts.append("[HISTORICAL CONTEXT — use to detect recurring patterns and escalations]")
            parts.append(memory_context)
            parts.append("---\n")

        parts.append("Analyze the following news articles grouped by category:\n")
        for category, articles in articles_by_category.items():
            parts.append(f"=== {category.upper()} ===")
            for i, a in enumerate(articles, 1):
                summary = a.get("summary", "")[:300]
                score = a.get("score", "N/A")
                parts.append(f"{i}. [{a['source']}] {a['title']} (Impact Score: {score})")
                if summary:
                    parts.append(f"   {summary}")
            parts.append("")

        return "\n".join(parts)
