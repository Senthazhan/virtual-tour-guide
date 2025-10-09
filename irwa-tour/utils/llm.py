import os
from typing import Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def polish_text(text: str, max_len: int = 600) -> str:
    if not text:
        return text
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = f"Rewrite this response to be concise, friendly, and factual (no extra info):\n{text}"
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"You are a concise assistant."},
                          {"role":"user","content":prompt}],
                max_tokens=220,
                temperature=0.2,
            )
            out = res.choices[0].message.content.strip()
            return out[:max_len]
        except Exception:
            pass
    import re
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sents[:5])[:max_len]
