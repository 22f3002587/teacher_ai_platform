import os
import re
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from groq import RateLimitError, APIStatusError

load_dotenv()

groq_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


def _extract_wait_seconds(error_message: str, default: float = 3.0) -> float:
    match = re.search(r"try again in ([\d.]+)(m?s)", str(error_message))
    if not match:
        return default
    value, unit = match.groups()
    value = float(value)
    return value / 1000 if unit == "ms" else value


def invoke_with_fallback(chain_input: dict, prompt_template, max_tokens: int = 1500, retries: int = 4):
    """
    Calls Groq. On rate-limit, waits the exact time Groq tells us to wait
    (parsed from the error message) plus a small buffer, then retries.
    No cross-provider fallback — Gemini free tier proved unreliable.
    """
    chain = prompt_template | groq_llm.bind(max_tokens=max_tokens)

    for attempt in range(retries):
        try:
            return chain.invoke(chain_input)
        except (RateLimitError, APIStatusError) as e:
            wait_time = _extract_wait_seconds(str(e)) + 0.5  # small buffer
            print(f"[llm_client] Groq rate-limited (attempt {attempt + 1}/{retries}), waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

    return chain.invoke(chain_input)