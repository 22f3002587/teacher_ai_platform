import json
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """You are a curriculum planner. Given this structured knowledge JSON extracted from an educational document, create a 5-period teaching plan.

Return ONLY a JSON object (no markdown, no extra text) in this exact format:

{{
  "periods": [
    {{
      "period_number": 1,
      "objectives": ["string", "..."],
      "concepts": ["string", "..."],
      "time_allocation": "string",
      "activities": ["string", "..."]
    }}
  ]
}}

There must be exactly 5 periods. Distribute the concepts, definitions, and formulae across periods in a logical teaching sequence (foundational concepts first, applications later). Use the misconceptions provided to inform activities that address them.

Knowledge JSON:
{knowledge_json}"""
)

class TeachingPlanner:
    def plan(self, knowledge_json: dict) -> dict:
        response = invoke_with_fallback(
            {"knowledge_json": json.dumps(knowledge_json)[:3500]},
            prompt,
            max_tokens=1000
        )

        raw = response.content.strip().replace("```json", "").replace("```", "")
        try:
            return json.loads(raw, strict=False)
        except json.JSONDecodeError:
            return {"error": "parse_failed", "raw_output": raw}