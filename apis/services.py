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

def call_together_inference(prompt: str, max_tokens: int = 512, temperature: float = 0.2):
    """
    Generic call to Together AI inference endpoint. Replace request format to match
    the endpoint's expected JSON if needed.
    """
    if not TOGETHER_API_URL or not TOGETHER_API_KEY:
        raise RuntimeError("Together API URL or API key not configured. Set TOGETHER_API_URL and TOGETHER_API_KEY.")

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Example body — you will likely need to adjust to Together's exact API schema.
    body = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        # add model, stop sequences, or other provider-specific fields as required
    }

    resp = requests.post(TOGETHER_API_URL, headers=headers, json=body, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    # The actual response structure depends on Together's API — adjust accordingly.
    # Here we assume the generated text is in data["text"] or data["output"].
    if "text" in data:
        return data["text"]
    if "output" in data:
        # e.g., {"output": {"generated_text": "..."}}
        out = data["output"]
        if isinstance(out, dict):
            # look for common keys
            for key in ("generated_text", "text", "content"):
                if key in out:
                    return out[key]
            # fallback: dump object
            return json.dumps(out)
        # or a simple string
        return str(out)
    # fallback: stringify
    return json.dumps(data)
