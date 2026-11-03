import os
import json
import time
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.8-flash"

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=30000),  # 30 seconds
)


def call_gemini_json(prompt, system_instruction, retries=3, temperature=0.1):
    """
    Call Gemini and return a parsed JSON dict.
    Retries on errors or invalid JSON; returns a structured fallback if all attempts fail.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
            return json.loads(response.text)

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt}/{retries} failed: {last_error[:120]}")

            # Permanent errors: retrying won't help, stop immediately
            if "429" in last_error or "404" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                break

            if attempt < retries:
                time.sleep(2 ** attempt)

    return {
        "error": "Service unavailable, please try again later.",
        "details": last_error,
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