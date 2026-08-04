import json
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """Read this document excerpt and return ONLY a JSON object (no markdown, no extra text) with these fields:
{{
  "subject": "string",
  "grade": "string",
  "difficulty": "Beginner | Intermediate | Advanced",
  "topic": "string",
  "chapter": "string",
  "language": "string"
}}

Document:
{document_text}"""
)

class EducationalClassifier:
    def classify(self, text: str) -> dict:
        response = invoke_with_fallback(
            {"document_text": text[:5000]},
            prompt,
            max_tokens=300
        )

        raw = response.content.strip().replace("```json", "").replace("```", "")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "parse_failed", "raw_output": raw}