import os
import json
import time
from google import genai
from google.genai import types

# النماذج بالترتيب: إذا فشل واحد (ضغط/كوتا/غير موجود) بننتقل للتالي.
# الكوتا المجانية لكل نموذج لحاله، فكل نموذج إله حد يومي منفصل.
MODELS = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
]

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=30000),  # 30 seconds
)


def _is_model_level_error(err: str) -> bool:
    """أخطاء بتخلينا ننتقل للنموذج التالي مباشرة بدون إعادة محاولة."""
    return any(
        s in err
        for s in ("429", "404", "RESOURCE_EXHAUSTED", "NOT_FOUND")
    )


def call_gemini_json(prompt, system_instruction, retries=2, temperature=0.1):
    """
    Call Gemini and return a parsed JSON dict.
    For each model: retry on temporary errors / invalid JSON.
    If a model hits quota (429) or is not found (404), move to the next model.
    Returns a structured fallback only if ALL models fail.
    """
    errors = {}

    for model in MODELS:
        for attempt in range(1, retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=temperature,
                    ),
                )
                result = json.loads(response.text)
                if isinstance(result, dict):
                    result["model_used"] = model
                return result

            except Exception as e:
                err = str(e)
                errors[model] = err[:200]
                print(f"[{model}] attempt {attempt}/{retries} failed: {err[:120]}")

                if _is_model_level_error(err):
                    break  # ما بينفع نعيد على نفس النموذج
                if attempt < retries:
                    time.sleep(2 ** attempt)

        print(f"[fallback] switching away from {model}")

    return {
        "error": "Service unavailable, please try again later.",
        "details": errors,
        "fallback": True,
    }


def summarize_to_json(data_text):
    """Summarize analytics text into a structured JSON dict."""
    system_instruction = (
        "You are a data analyst assistant. Use ONLY the data provided. "
        "Do not invent numbers or facts that are not in the data."
    )

    prompt = f"""Summarize the following data.

Data:
{data_text}

Return a JSON object with exactly these keys:
- "summary": one or two short sentences
- "key_insight": the single most important finding
- "confidence": "high", "medium", or "low" (based on how much data was given)
"""

    return call_gemini_json(prompt, system_instruction, temperature=0.2)


def answer_from_context(question, retrieved_chunks):
    """Answer a question using ONLY the retrieved chunks, as structured JSON."""
    context = "\n\n".join(
        f"[Source: {c['chunk']['source_document']}]\n{c['chunk']['text']}"
        for c in retrieved_chunks
    )

    system_instruction = (
        "You answer questions using ONLY the provided context. "
        "If the context does not contain the answer, set found to false "
        "and answer to 'I don't have enough information to answer that.' "
        "Never use outside knowledge."
    )

    prompt = f"""Context:
{context}

Question: {question}

Return a JSON object with exactly these keys:
- "answer": a short, direct answer in one or two sentences
- "source": the source document name the answer came from, or null if not found
- "found": true if the context contains the answer, otherwise false
"""

    return call_gemini_json(prompt, system_instruction, temperature=0.1)