import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """You are a teacher creating an assessment for one class period.

Given this period plan, generate a complete assessment. Return ONLY a JSON object (no markdown, no extra text) in this exact format:

{{
  "mcqs": [{{"question": "string", "options": ["string","string","string","string"], "correct_option": "string"}}],
  "short_answer": [{{"question": "string", "expected_answer": "string"}}],
  "long_answer": [{{"question": "string", "expected_answer": "string"}}],
  "numericals": [{{"question": "string", "solution": "string", "final_answer": "string"}}],
  "rubrics": [{{"criterion": "string", "description": "string", "max_marks": "number"}}],
  "answer_key": {{"mcqs": ["string"], "short_answer": ["string"], "long_answer": ["string"], "numericals": ["string"]}}
}}

Do not use backslashes for multiplication or any symbol (write "2 * 3", never "2 \\* 3"). Keep numerical solutions to 2-3 sentences max. Generate at least 2 MCQs, 1 short answer, 1 long answer, 1 numerical (empty list if purely non-mathematical).

Period plan:
{period_json}"""
)


def sanitize_json_escapes(raw: str) -> str:
    return re.sub(r'\\(?!["\\/bfnrtu])', '', raw)


def _generate_one(period: dict) -> dict:
    response = invoke_with_fallback(
        {"period_json": json.dumps(period)},
        prompt,
        max_tokens=1300
    )
    raw = response.content.strip().replace("```json", "").replace("```", "")
    raw = sanitize_json_escapes(raw)
    try:
        assessment = json.loads(raw, strict=False)
    except json.JSONDecodeError:
        assessment = {"error": "parse_failed", "raw_output": raw}
    return {"period_number": period.get("period_number"), "assessment": assessment}


class AssessmentGenerator:
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

        return {"assessments": results}