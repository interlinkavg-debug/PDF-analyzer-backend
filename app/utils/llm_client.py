"""
LLM client abstraction using the Openrouter HTTP API.

This module provides a single async function `call_llm_api` that:
 - is decorated with timeout and retry guards (configurable via Settings)
 - calls the Openrouter Chat Completions endpoint using httpx.AsyncClient
 - returns the textual response (trimmed) or raises on unrecoverable errors

Notes:
 - We avoid importing the synchronous `openrouter` SDK to keep this async and
   to make retries/timeouts actionable at the HTTP layer.
 - The function is conservative about logging and never prints the API key.
"""

import logging
from typing import Optional

import httpx

from app.utils.config import settings
from app.utils.decorators import async_retry, async_timeout

logger = logging.getLogger(__name__)

# model used
MODEL = settings.LLM_MODEL_NAME


@async_retry(settings.LLM_MAX_RETRIES)
@async_timeout(settings.LLM_TIMEOUT_SECONDS)
async def call_llm_api(
    prompt: str,
    model: str = MODEL,
    max_tokens: int = 500,
    temperature: float = 0.2,
) -> dict:
    """
    Call the Openrouter Chat Completions REST API asynchronously and return the
    assistant reply text.

    Args:
        prompt: The user prompt to send to the LLM.
        model: Model id (e.g. "gpt-3.5-turbo" or "gpt-4").
        max_tokens: Max tokens to request (the LLM provider enforces limits).
        temperature: Sampling temperature.

    Returns:
        dict: {
            'summary': str,
            'prompt_tokens': int,
            'completion_tokens': int,
            'total_tokens': int,
            'estimated_cost': float
        }

    Raises:
        httpx.HTTPError or RuntimeError on non-recoverable failures.
    """
    # Build request payload
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    url = "https://openrouter.ai/api/v1/chat/completions"


    # Use a short-lived AsyncClient per request; the decorators handle retries/timeouts
    # httpx timeout is a safety net; the async_timeout decorator is high-level guard.
    timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS, connect=settings.LLM_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            logger.debug("Calling LLM API (masked key %s...)", settings.OPENROUTER_API_KEY[:4] + "****" + settings.OPENROUTER_API_KEY[-4:])
            resp = await client.post(url, json=payload, headers=headers)

            # Raise for non-2xx to trigger retry logic (if applicable)
            resp.raise_for_status()

            data = resp.json()


            # Standard ChatCompletion response parsing:
            # try the new Chat structure first
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                # Chat API uses choice["message"]["content"]
                if "message" in choice and isinstance(choice["message"], dict) and "content" in choice["message"]:
                    content = choice["message"]["content"]
                # older formats or alternative endpoints may have "text"
                elif "text" in choice:
                    content = choice["text"]
                else:
                    raise RuntimeError("LLM response has no 'message.content' or 'text' field.")
            else:
                raise RuntimeError("Unexpected LLM response structure: no 'choices'.")

            # Ensure string, strip whitespace
            if not isinstance(content, str):
                content = str(content)
            summary = content.strip()
            logger.debug("LLM API returned %d characters.", len(summary))

            # Token usage and cost estimation
            prompt_tokens = None
            completion_tokens = None
            total_tokens = None
            estimated_cost = None
            if "usage" in data:
                prompt_tokens = data["usage"].get("prompt_tokens")
                completion_tokens = data["usage"].get("completion_tokens")
                total_tokens = data["usage"].get("total_tokens")
                # Example cost calculation (adjust per your LLM provider's pricing)
                # For OpenAI GPT-3.5: $0.0015/1K prompt, $0.002/1K completion
                if prompt_tokens is not None and completion_tokens is not None:
                    estimated_cost = (prompt_tokens / 1000 * 0.0015) + (completion_tokens / 1000 * 0.002)

            return {
                "summary": summary,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": estimated_cost
            }

        except httpx.RequestError as e:
            # Network-level issues (DNS, connection reset, etc.)
            logger.warning("Network error when calling LLM API: %s", str(e))
            raise

        except httpx.HTTPStatusError as e:
            # Non-2xx returned; include status and text for diagnostics (do NOT log secrets)
            status = e.response.status_code
            body_snippet = (e.response.text[:400] + "...") if e.response.text else ""
            logger.error("LLM API returned HTTP %d: %s", status, body_snippet)
            raise RuntimeError(f"LLM API returned HTTP {status}: {body_snippet}") from e

        except Exception as e:
            # Generic fallback
            logger.error("Unexpected error during LLM call: %s", str(e))
            raise
