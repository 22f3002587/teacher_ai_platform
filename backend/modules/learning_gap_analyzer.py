import json
import re
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """You are an education expert analyzing learning gaps for a document's content.

Given this list of misconceptions found in the document, analyze each one. Return ONLY a JSON object (no markdown, no extra text, no backslash escapes for symbols like * or /) in this exact format:

{{
  "gap_analysis": [
    {{
      "misconception": "string",
      "severity": "Low | Medium | High",
      "diagnostic_question": "string",
      "remedial_action": "string"
    }}
  ]
}}

If the misconceptions list is empty, return an empty gap_analysis list.

Misconceptions:
{misconceptions_json}"""
)


def sanitize_json_escapes(raw: str) -> str:
    return re.sub(r'\\(?!["\\/bfnrtu])', '', raw)


class LearningGapAnalyzer:
    def analyze(self, knowledge: dict) -> dict:
        misconceptions = knowledge.get("misconceptions", [])
        response = invoke_with_fallback(
            {"misconceptions_json": json.dumps(misconceptions)},
            prompt,
            max_tokens=1000
        )

        raw = response.content.strip().replace("```json", "").replace("```", "")
        raw = sanitize_json_escapes(raw)

        try:
            return json.loads(raw, strict=False)
        except json.JSONDecodeError:
            return {"error": "parse_failed", "raw_output": raw}