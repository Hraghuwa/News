import os
import re
import json
import math
import logging
import tempfile
import datetime
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory.json")
LOOKBACK_DAYS = 30
TOP_K = 4
MIN_SIMILARITY = 0.05


class RAGMemory:
    def load(self) -> dict:
        path = os.path.abspath(MEMORY_PATH)
        if not os.path.exists(path):
            logger.info("memory.json not found. Starting fresh.")
            return {"version": 2, "entries": []}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load memory.json: {e}. Starting fresh.")
            return {"version": 2, "entries": []}

    def save(self, store: dict) -> None:
        path = os.path.abspath(MEMORY_PATH)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            dir_ = os.path.dirname(path)
            with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp", encoding="utf-8") as f:
                json.dump(store, f, ensure_ascii=False, indent=2)
                tmp_path = f.name
            os.replace(tmp_path, path)
        except OSError as e:
            logger.error(f"Failed to save memory.json: {e}")

    def append_run(
        self,
        date: str,
        sector_expert_output: dict[str, Any],
        contrarian_output: dict[str, Any],
        impact_scores: list[dict],
    ) -> None:
        store = self.load()
        entries = store.get("entries", [])

        for sector, data in sector_expert_output.items():
            if not isinstance(data, dict):
                continue
            contrarian = contrarian_output.get(sector, {})
            # Extract top scored articles for this entry's context
            sector_scores = [
                {"title": a["title"], "score": a.get("score", 0), "is_black_swan": a.get("is_black_swan", False)}
                for a in impact_scores
                if a.get("category") == sector or a.get("source") in sector
            ][:5]

            entry = {
                "date": date,
                "sector": sector,
                "headline_themes": self._extract_themes(data),
                "expert_summary": data.get("summary", "")[:500],
                "emerging_narrative": data.get("emerging_narrative", "")[:300],
                "contrarian_note": contrarian.get("one_liner", "")[:300],
                "impact_scores": sector_scores,
                "tags": self._extract_tags(sector, data),
            }
            entries.insert(0, entry)

        # Keep only last 90 days worth (cap at 1000 entries to avoid file bloat)
        entries = entries[:1000]
        store["entries"] = entries
        self.save(store)
        logger.info(f"Memory updated with {len(sector_expert_output)} new entries.")

    def retrieve_context(self, query: str) -> str:
        store = self.load()
        entries = self._recent_entries(store)
        if not entries:
            return ""

        corpus = [
            f"{e.get('expert_summary', '')} {e.get('emerging_narrative', '')} {' '.join(e.get('tags', []))}"
            for e in entries
        ]
        scores = self._tfidf_cosine(query, corpus)

        ranked = sorted(zip(scores, entries), key=lambda x: x[0], reverse=True)
        top = [(s, e) for s, e in ranked if s >= MIN_SIMILARITY][:TOP_K]

        if not top:
            return ""

        lines = []
        for _, e in top:
            date = e.get("date", "?")
            sector = e.get("sector", "?")
            summary = e.get("expert_summary", "")[:200]
            contrarian = e.get("contrarian_note", "")
            line = f"• [{date} | {sector}] {summary}"
            if contrarian:
                line += f"\n  CONTRARIAN: {contrarian}"
            lines.append(line)

        return "\n".join(lines)

    def _recent_entries(self, store: dict) -> list[dict]:
        cutoff = (datetime.date.today() - datetime.timedelta(days=LOOKBACK_DAYS)).isoformat()
        return [e for e in store.get("entries", []) if e.get("date", "") >= cutoff]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z]{2,}", text.lower())

    def _tfidf_cosine(self, query: str, corpus: list[str]) -> list[float]:
        docs = [self._tokenize(doc) for doc in corpus]
        query_tokens = self._tokenize(query)
        if not query_tokens or not docs:
            return [0.0] * len(corpus)

        # Build IDF
        n = len(docs)
        df: Counter = Counter()
        for doc in docs:
            for term in set(doc):
                df[term] += 1

        def idf(term):
            return math.log((n + 1) / (df.get(term, 0) + 1)) + 1

        def tfidf_vec(tokens):
            tf = Counter(tokens)
            total = max(len(tokens), 1)
            return {t: (tf[t] / total) * idf(t) for t in tf}

        q_vec = tfidf_vec(query_tokens)
        q_norm = math.sqrt(sum(v ** 2 for v in q_vec.values())) or 1.0

        similarities = []
        for doc in docs:
            d_vec = tfidf_vec(doc)
            d_norm = math.sqrt(sum(v ** 2 for v in d_vec.values())) or 1.0
            dot = sum(q_vec.get(t, 0) * d_vec.get(t, 0) for t in q_vec)
            similarities.append(dot / (q_norm * d_norm))
        return similarities

    @staticmethod
    def _extract_themes(data: dict) -> list[str]:
        narrative = data.get("emerging_narrative", "")
        summary = data.get("summary", "")
        words = re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", narrative + " " + summary)
        return list(dict.fromkeys(words))[:8]

    @staticmethod
    def _extract_tags(sector: str, data: dict) -> list[str]:
        tags = [sector]
        tags.extend(data.get("affected_sectors", []))
        lenses = data.get("lenses", {})
        for text in lenses.values():
            words = re.findall(r"\b[A-Z]{2,}\b", str(text))
            tags.extend(words[:3])
        return list(dict.fromkeys(tags))[:15]
