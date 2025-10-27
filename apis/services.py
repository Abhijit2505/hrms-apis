# jdgen/services.py
import os
import json
import requests
from django.conf import settings

# config: set these in env or Django settings
TOGETHER_API_URL = getattr(settings, "TOGETHER_API_URL", os.getenv("TOGETHER_API_URL"))
TOGETHER_API_KEY = getattr(settings, "TOGETHER_API_KEY", os.getenv("TOGETHER_API_KEY"))

DEFAULT_TIMEOUT = 30  # seconds

def build_prompt(payload: dict, word_count: int = 300, tone: str = "Professional", title: str = "", language: str = "English"):
    """
    Build a clear instruction prompt for the model. We embed the payload as JSON
    and ask the model to produce a polished, professional Job Description of
    approximately `word_count` words.
    """
    pretty_payload = json.dumps(payload, indent=2, ensure_ascii=False)
    title_section = f"Title: {title}\n\n" if title else ""
    prompt = (
        f"You are an expert technical recruiter and professional copywriter.\n\n"
        f"{title_section}"
        f"Below is structured input describing a role and related details. Use all relevant fields\n"
        f"from the JSON to produce a professional, well-formatted Job Description (JD) in {language}.\n\n"
        f"Requirements for the JD:\n"
        f"- Tone: {tone}\n"
        f"- Target length: ~{word_count} words. Focus on clarity and completeness; hitting exact words is not required but try to be close.\n"
        f"- Include sections: Summary, Responsibilities, Required Qualifications, Preferred Qualifications, About the Company (if company info exists), and How to Apply.\n"
        f"- If the JSON contains fields like `skills`, `experience`, `location`, `salary`, `benefits`, or `company`, integrate them sensibly into the JD.\n"
        f"- Use professional language and bullet points where appropriate.\n\n"
        f"INPUT JSON:\n{pretty_payload}\n\n"
        f"Output only the Job Description text (no additional commentary). Start with a short one-line title header followed by the sections.\n"
    )
    return prompt

import os
import json
import requests
from typing import List, Dict, Optional
import certifi
import requests

DEFAULT_TIMEOUT = 30
# TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
# # You can set TOGETHER_API_URL to "https://api.together.xyz/v1/chat/completions"
# # or leave it None and we'll use the canonical endpoint below.
# TOGETHER_API_URL = os.environ.get("TOGETHER_API_URL") or "https://api.together.xyz/v1/chat/completions"

def call_together_inference(
    user_prompt: str,
    model: str = "openai/gpt-oss-20b",
    max_tokens: int = 512,
    temperature: float = 0.2,
    system_prompt: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Call Together AI chat/completions (OpenAI-compatible chat endpoint).
    Returns the assistant text (first choice). Raises RuntimeError on failure with helpful info.
    """
    if not TOGETHER_API_KEY:
        raise RuntimeError("TOGETHER_API_KEY not configured in environment.")

    # Build messages array per OpenAI-compatible chat format
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        resp = requests.post(TOGETHER_API_URL, headers=headers, json=body, timeout=timeout, verify=certifi.where())
    except requests.RequestException as e:
        raise RuntimeError(f"Network error calling Together API: {e}") from e

    # Helpful debug for non-2xx responses
    if resp.status_code >= 400:
        snippet = resp.text[:1000]  # avoid huge dumps
        raise RuntimeError(
            f"Together API returned {resp.status_code}: {resp.reason}. "
            f"Response body (truncated): {snippet}"
        )

    data = resp.json()

    # Typical OpenAI-compatible response: choices -> [ { message: { content: "..." } } ]
    if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
        choice = data["choices"][0]
        # new format: choice.message.content
        if "message" in choice and isinstance(choice["message"], dict):
            content = choice["message"].get("content")
            if content:
                return content
        # older/alternate: choice.text
        if "text" in choice and isinstance(choice["text"], str):
            return choice["text"]

    # Some services return top-level 'output' or 'text'
    for k in ("text", "output", "generated_text"):
        if k in data:
            # output could be dict or string
            out = data[k]
            if isinstance(out, str):
                return out
            if isinstance(out, dict):
                # try to find content keys
                for kk in ("generated_text", "text", "content"):
                    if kk in out and isinstance(out[kk], str):
                        return out[kk]
                return json.dumps(out)

    # Fallback: return full response as JSON string
    return json.dumps(data)
