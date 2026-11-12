import time

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from week10_tools import log, query_cost_table, search_documents, summarize_result

MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",   # الأخير: عليه ضغط وبيضيّع وقت بالـ timeout
]

TOOLS = [search_documents, query_cost_table, summarize_result]
TOOL_MAP = {t.name: t for t in TOOLS}

SYSTEM_PROMPT = """You are a data + documents assistant for a retail company.
You have three tools:
- search_documents: for policies, rules, invoices, FAQs and reports.
- query_cost_table: for numeric questions (sales, profit, margins, rankings).
- summarize_result: use ONLY if a tool result is longer than ~1500 characters.
  For short results, answer directly without calling it.

Rules:
1. Answer ONLY from tool results. Never use outside knowledge.
2. Always mention the source (document name, or the SQL table/view used).
3. If the tool results do not contain the answer, or the question is not
   about the company's data or documents, say: "I don't have enough
   information to answer that." Do not guess.
4. For policy questions about a specific percentage, call search_documents
   with k=3 so you see enough context.
5. If a question mentions a month or period without a year, say in your
   answer which years/date range the SQL result covers, or state that the
   documents refer to a specific year. Never present an all-years
   aggregate as if it were one specific year.
6. The sales database covers orders from 2014-01-03 to 2017-12-30 only.
   The documents (invoices, reports, policies) refer to 2024. They come
   from different sources and periods, so never mix or compare them as if
   they cover the same time.
"""

# كل نموذج مربوط بالأدوات، وإذا فشل واحد بننتقل للتالي تلقائياً
_llms = [
    ChatGoogleGenerativeAI(
        model=m, temperature=0, timeout=30, max_retries=1
    ).bind_tools(TOOLS)
    for m in MODELS
]
llm = _llms[0].with_fallbacks(_llms[1:])


def ask_with_trace(question: str, max_steps: int = 5) -> dict:
    """نفس ask لكن بيرجع تفاصيل: الأدوات المستخدمة، النموذج، عدد الخطوات، الوقت."""
    start = time.time()
    log.info(f"[agent] question: {question!r}")
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]
    tools_used, model_used = [], "unknown"

    def result(answer, steps):
        return {
            "answer": answer,
            "tools_used": tools_used,
            "model": model_used,
            "steps": steps,
            "seconds": round(time.time() - start, 1),
        }

    for step in range(1, max_steps + 1):
        try:
            ai = llm.invoke(messages)
        except Exception as e:
            log.error(f"[agent] all models failed at step {step}: {str(e)[:150]}")
            return result("Service unavailable, please try again later.", step)

        model_used = (getattr(ai, "response_metadata", {}) or {}).get(
            "model_name", model_used
        )
        messages.append(ai)

        if not ai.tool_calls:
            log.info(f"[agent] final answer after {step} step(s), "
                     f"{time.time() - start:.1f}s, model={model_used}")
            return result(ai.text, step)

        for tc in ai.tool_calls:
            log.info(f"[agent] step {step}: model chose tool={tc['name']} args={tc['args']}")
            tools_used.append(tc["name"])
            tool_fn = TOOL_MAP.get(tc["name"])
            if tool_fn is None:
                out = '{"error": "unknown tool"}'
            else:
                out = tool_fn.invoke(tc["args"])
            messages.append(
                ToolMessage(content=out, tool_call_id=tc["id"], name=tc["name"])
            )

    log.warning("[agent] reached max_steps without a final answer")
    return result("I couldn't finish answering within the allowed steps.", max_steps)


def ask(question: str, max_steps: int = 5) -> str:
    return ask_with_trace(question, max_steps)["answer"]


if __name__ == "__main__":
    # 3 أسئلة بس لتوفير الكوتا (كل سؤال = 2 إلى 3 طلبات)
    questions = [
        "What is the discount policy for furniture?",      # وثائق
        "Which region had the highest total sales?",       # SQL
        "What is the capital of France?",                  # خارج الموضوع
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print("A:", ask(q))