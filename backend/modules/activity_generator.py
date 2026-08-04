import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """You are a teacher designing hands-on classroom activities for one class period.

Given this period plan, generate one activity of each of these four types: Experiment, Role Play, Group Discussion, and Demonstration. Return ONLY a JSON object (no markdown, no extra text) in this exact format:

{{
  "experiment": {{"title": "string", "materials": ["string"], "instructions": ["string"], "duration": "string", "success_criteria": ["string"]}},
  "role_play": {{"title": "string", "materials": ["string"], "instructions": ["string"], "duration": "string", "success_criteria": ["string"]}},
  "group_discussion": {{"title": "string", "materials": ["string"], "instructions": ["string"], "duration": "string", "success_criteria": ["string"]}},
  "demonstration": {{"title": "string", "materials": ["string"], "instructions": ["string"], "duration": "string", "success_criteria": ["string"]}}
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
        activities = json.loads(raw, strict=False)
    except json.JSONDecodeError:
        activities = {"error": "parse_failed", "raw_output": raw}
    return {"period_number": period.get("period_number"), "activities": activities}


class ActivityGenerator:
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

        return {"activity_sets": results}