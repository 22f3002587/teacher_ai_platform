import json
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_client import invoke_with_fallback

prompt = ChatPromptTemplate.from_template(
    """Read this educational document and extract structured knowledge from it.
Return ONLY a JSON object (no markdown, no extra text) with these fields:

{{
  "learning_objectives": ["string", "..."],
  "prerequisites": ["string", "..."],
  "definitions": [
    {{"term": "string", "definition": "string"}}
  ],
  "formulae": [
    {{"name": "string", "formula": "string", "description": "string"}}
  ],
  "examples": ["string", "..."],
  "applications": ["string", "..."],
  "keywords": ["string", "..."],
  "misconceptions": ["string", "..."]
}}

Limit yourself to at most 8 of the most important definitions and 3 formulae — do not try to list every term in the document. If a section genuinely doesn't apply, return an empty list for it.

Document:
{document_text}"""
)

class KnowledgeExtractor:
    def extract(self, text: str) -> dict:
        response = invoke_with_fallback(
            {"document_text": text[:3500]},
            prompt,
            max_tokens=4000
        )

        raw = response.content.strip().replace("```json", "").replace("```", "")
        try:
            return json.loads(raw, strict=False)
        except json.JSONDecodeError:
            return {"error": "parse_failed", "raw_output": raw}