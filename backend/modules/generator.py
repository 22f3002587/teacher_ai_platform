import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """You are a teacher preparing a detailed lesson for one class period.

Given this period plan, generate a complete lesson. Return ONLY a JSON object (no markdown, no extra text) in this exact format:

{{
  "entry_ticket": "string",
  "teacher_script": "string",
  "blackboard_notes": "string",
  "activities": ["string", "..."],
  "checkpoint_questions": ["string", "..."],
  "exit_ticket": "string",
  "homework": "string",
  "mentor_moment": "string"
}}

Period plan:
{period_json}"""
)


def _generate_one(period: dict) -> dict:
    response = invoke_with_fallback(
        {"period_json": json.dumps(period)},
        prompt,
        max_tokens=900
    )
    raw = response.content.strip().replace("```json", "").replace("```", "")
    try:
        lesson = json.loads(raw, strict=False)
    except json.JSONDecodeError:
        lesson = {"error": "parse_failed", "raw_output": raw}
    return {"period_number": period.get("period_number"), "lesson": lesson}


class LessonGenerator:
    def generate(self, teaching_plan: dict, max_workers: int = 3) -> dict:
        periods = teaching_plan.get("periods", [])
        results = [None] * len(periods)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(_generate_one, period): i
                for i, period in enumerate(periods)
            }
            for future in as_completed(future_to_index):
                i = future_to_index[future]
                results[i] = future.result()

        return {"lessons": results}