"""
InsightFlow AI — Nemotron Service

Connects to NVIDIA Nemotron 3 Ultra via OpenRouter.
OpenRouter provides an OpenAI-compatible API, so we use the
standard openai Python client with a custom base_url.

Model: nvidia/nemotron-3-ultra-550b-a55b:free
Endpoint: https://openrouter.ai/api/v1
"""

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root (two levels up from this file)
load_dotenv()

# ── OpenRouter Client ─────────────────────────────────────────────────────────

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Model ID from OpenRouter
MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

# ── InsightFlow AI System Prompt ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are InsightFlow AI Assistant — an intelligent data analysis helper.

CRITICAL INSTRUCTION: You MUST NEVER output any internal monologue, reasoning, or "thinking" steps (e.g., "The user is asking for...", "Let me scan...", "I need to..."). ALWAYS respond directly and ONLY with the final formatted answer or table requested.

Your job is to help users understand their uploaded datasets, preprocessing operations,
EDA (Exploratory Data Analysis) results, and visualizations.

Guidelines:
- Give clear, simple, and accurate explanations.
- When dataset context is provided, use it to answer questions specifically.
- Do NOT invent or guess dataset statistics — only use what is explicitly provided.
- If information is not available in the context, clearly say so.
- Keep answers concise but thorough.
- Use bullet points or numbered lists when helpful.
- You can suggest best practices for data cleaning, preprocessing, and analysis.
"""


# ── Core Function ─────────────────────────────────────────────────────────────

def generate_response(messages: list[dict]) -> str:
    """
    Send a list of messages to NVIDIA Nemotron 3 Ultra via OpenRouter.

    Args:
        messages: List of dicts with 'role' and 'content' keys.
                  Roles: 'system', 'user', 'assistant'

    Returns:
        The AI-generated response as a string.

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set.
        Exception: If the API call fails.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. "
            "Please add it to your .env file at the project root."
        )

    import re

    # Retry up to 3 times for rate-limit / 503 errors from OpenRouter free tier
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=3000,  # Increased to prevent large table responses from being cut off
            )
            break  # success — exit retry loop
        except Exception as e:
            err_str = str(e).lower()
            if attempt < max_retries - 1 and ("503" in err_str or "rate" in err_str or "overload" in err_str):
                wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                time.sleep(wait)
                continue
            raise  # re-raise if not retryable or out of retries

    answer = response.choices[0].message.content
    # Strip <think>...</think> blocks if the model outputs them
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
    # Strip leftover trailing newline gaps
    answer = answer.strip()
    return answer


def chat_with_context(user_message: str, dataset_context: str = "") -> str:
    """
    Convenience wrapper: builds messages with system prompt + optional dataset context,
    then calls generate_response().

    Args:
        user_message: The user's question.
        dataset_context: Optional string describing the dataset (rows, columns, missing values, etc.)

    Returns:
        AI-generated response string.
    """
    system_content = SYSTEM_PROMPT

    if dataset_context:
        system_content += f"\n\nCurrent Dataset Context:\n{dataset_context}"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]

    return generate_response(messages)
