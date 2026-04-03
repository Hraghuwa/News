import os
import re
import json
import time
import logging

from groq import Groq

logger = logging.getLogger(__name__)

class BaseAgent:
    MODEL = "llama-3.3-70b-versatile"
    MAX_RETRIES = 3

    def __init__(self, name: str, temperature: float = 0.65):
        self.name = name
        self.temperature = temperature
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(f"GROQ_API_KEY not set — agent {self.name} cannot initialize.")
        self._client = Groq(api_key=api_key)

    def call(self, system_prompt: str, user_message: str, max_tokens: int = 3000, expect_json: bool = True) -> str:
        if expect_json:
            system_prompt += "\n\nRespond with valid JSON only. No markdown fences, no commentary."

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"[{self.name}] Groq call attempt {attempt + 1}...")
                response = self._client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=self.temperature,
                    max_tokens=max_tokens,
                )
                result = response.choices[0].message.content
                logger.info(f"[{self.name}] Call succeeded.")
                return result
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate_limit" in err_str.lower():
                    wait = 20 * (attempt + 1)
                    logger.warning(f"[{self.name}] Rate limit hit. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"[{self.name}] Groq error: {e}")
                    if attempt == self.MAX_RETRIES - 1:
                        raise
                    time.sleep(5)

        raise RuntimeError(f"[{self.name}] All {self.MAX_RETRIES} retries exhausted.")

    @staticmethod
    def parse_json(raw: str) -> dict:
        raw = raw.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse JSON from agent response. Returning empty dict.")
        return {}

    @staticmethod
    def parse_json_array(raw: str) -> list:
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse JSON array from agent response. Returning empty list.")
        return []
