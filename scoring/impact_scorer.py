import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

THRESHOLD = 80
BLACK_SWAN_THRESHOLD = 95

SYSTEM_PROMPT = """You are an expert news impact analyst. Score each article on a 1-100 scale.

Score = Magnitude (1-10) × Probability (1-10)
- Magnitude: How large could the real-world change be? (1=trivial, 10=world-changing)
- Probability: How likely is this to materialize within 6 months? (1=speculative, 10=near-certain)

Calibration:
- 95-100: Extremely rare. Reserve for genuine Black Swan events (financial crisis, war declaration, breakthrough tech)
- 80-94: Major market-moving story. Top 5% of daily news.
- 50-79: Important but not urgent. Worth monitoring.
- Below 50: Background noise. Most daily news falls here.

Return a JSON array with one object per article IN THE SAME ORDER as the input:
[
  {
    "score": 85,
    "magnitude": 9,
    "probability": 9,
    "reasoning": "one sentence explaining the score",
    "is_black_swan": false
  }
]"""


class ImpactScorer(BaseAgent):
    def __init__(self):
        super().__init__(name="ImpactScorer", temperature=0.3)

    def score_all(self, articles: list[dict]) -> tuple[list[dict], list[dict]]:
        if not articles:
            return [], []

        prompt = self._build_scoring_prompt(articles)
        raw = self.call(SYSTEM_PROMPT, prompt, max_tokens=3000)
        scores = self.parse_json_array(raw)

        all_scored = self._apply_scores(articles, scores)
        high_impact = [a for a in all_scored if a.get("score", 0) >= THRESHOLD]
        high_impact.sort(key=lambda x: x.get("score", 0), reverse=True)

        logger.info(f"Scored {len(all_scored)} articles. {len(high_impact)} passed threshold ({THRESHOLD}+). Black swans: {sum(1 for a in all_scored if a.get('is_black_swan'))}.")
        return high_impact, all_scored

    def _build_scoring_prompt(self, articles: list[dict]) -> str:
        lines = [f"Score these {len(articles)} news articles:\n"]
        for i, a in enumerate(articles, 1):
            summary = a.get("summary", "")[:250]
            lines.append(f"{i}. [{a['source']}] {a['title']}")
            if summary:
                lines.append(f"   {summary}")
        return "\n".join(lines)

    def _apply_scores(self, articles: list[dict], scores: list[dict]) -> list[dict]:
        result = []
        for i, article in enumerate(articles):
            scored = dict(article)
            if i < len(scores) and isinstance(scores[i], dict):
                s = scores[i]
                mag = max(1, min(10, int(s.get("magnitude", 5))))
                prob = max(1, min(10, int(s.get("probability", 5))))
                computed = mag * prob
                scored["score"] = computed
                scored["magnitude"] = mag
                scored["probability"] = prob
                scored["reasoning"] = s.get("reasoning", "")
                scored["is_black_swan"] = computed >= BLACK_SWAN_THRESHOLD
            else:
                # Default: low score so it doesn't pollute the pipeline
                scored["score"] = 9
                scored["magnitude"] = 3
                scored["probability"] = 3
                scored["reasoning"] = "Score unavailable."
                scored["is_black_swan"] = False
            result.append(scored)
        return result
