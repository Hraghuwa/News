import logging
from typing import Any
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional contrarian analyst. Your only job is to find what the consensus misses.

Rules:
- The most valuable insight is what 95% of readers will NOT see.
- Every panic has a hidden silver lining. Every euphoria hides a landmine.
- You are not negative for its own sake — you find asymmetric truth.
- Be specific. Name companies, countries, assets, or policies.
- Do NOT repeat what the expert already said.

For each sector analysis provided, return a JSON object where each key is the sector name and the value follows this schema:
{
  "blind_spot": "The key thing the consensus analysis is overlooking",
  "hidden_opportunity": "A counter-intuitive investment or business opportunity this news creates",
  "contrarian_bet": "The specific asymmetric trade or move a contrarian would make",
  "narrative_trap": "The dangerous assumption most people are making",
  "plausibility_score": 75,
  "one_liner": "Single punchy sentence summarizing the contrarian view"
}"""


class ContrarianAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Contrarian", temperature=0.85)

    def debate(self, expert_analyses: dict[str, Any]) -> dict[str, Any]:
        user_message = self._flatten_all_sectors(expert_analyses)
        raw = self.call(SYSTEM_PROMPT, user_message, max_tokens=2500)
        result = self.parse_json(raw)
        if not result:
            logger.warning("Contrarian returned empty insights. Using fallback.")
            result = {sector: {"blind_spot": "N/A", "hidden_opportunity": "N/A", "contrarian_bet": "N/A", "narrative_trap": "N/A", "plausibility_score": 50, "one_liner": "No contrarian view generated."} for sector in expert_analyses}
        return result

    def _flatten_all_sectors(self, expert_analyses: dict[str, Any]) -> str:
        lines = ["Here are the expert analyses for each sector. Find what each is missing:\n"]
        for sector, data in expert_analyses.items():
            if not isinstance(data, dict):
                continue
            summary = data.get("summary", "")
            narrative = data.get("emerging_narrative", "")
            lenses = data.get("lenses", {})
            lines.append(f"[SECTOR: {sector}]")
            lines.append(f"SUMMARY: {summary}")
            lines.append(f"NARRATIVE: {narrative}")
            if lenses:
                lens_str = " | ".join(f"{k}={v[:100]}" for k, v in lenses.items() if v)
                lines.append(f"LENSES: {lens_str}")
            lines.append("")
        return "\n".join(lines)
