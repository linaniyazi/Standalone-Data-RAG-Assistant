import json
import re
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from week10_tools import log, query_cost_table, search_documents

MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

MIN_DOC_SCORE = 0.15   # أقل درجة تشابه نعتبرها "في شي ذو صلة"


# ---------------------------------------------------------------
# State: كل النودات بتقرأ منه وبتكتب فيه
# ---------------------------------------------------------------
class State(TypedDict, total=False):
    question: str
    route: str          # docs | sql | fallback
    sql: str
    tool_output: str
    top_score: float
    valid: bool
    reason: str
    answer: str


# ---------------------------------------------------------------
# 1) Classifier بالقواعد (بدون LLM، بدون كوتا)
# ---------------------------------------------------------------
def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


STRONG_DOC = (r"\b(policy|policies|invoice|invoices|report|faq|approve|approval|"
              r"approver|penalty|payment|payments|process|accepted|refund)\b")
STRONG_DATA = (r"\b(sales|profit|profits|margin|margins|region|regions|category|"
               r"categories|sub-category|subcategory|quantity|revenue|average|sum|"
               r"count)\b|how many")
WEAK_DOC = r"\b(discount|discounts|late|order|orders)\b"


def classify_question(question: str) -> str:
    q = question.lower()
    if _has(STRONG_DOC, q):
        return "docs"
    if _has(STRONG_DATA, q):
        return "sql"
    if _has(WEAK_DOC, q):
        return "docs"
    return "fallback"


def classify(state: State) -> dict:
    route = classify_question(state["question"])
    log.info(f"[classify] route={route} question={state['question']!r}")
    return {"route": route}


# ---------------------------------------------------------------
# LLM مع fallback بين النماذج (بيتبني أول مرة بس)
# ---------------------------------------------------------------
_llm = None


def llm_text(system: str, user: str) -> str:
    global _llm
    if _llm is None:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llms = [ChatGoogleGenerativeAI(model=m, temperature=0, timeout=30,
                                       max_retries=1) for m in MODELS]
        _llm = llms[0].with_fallbacks(llms[1:])
    return _llm.invoke([SystemMessage(system), HumanMessage(user)]).text


# ---------------------------------------------------------------
# 2) مسار المستندات: بحث + تلميح من الـ metadata (نوع المستند)
# ---------------------------------------------------------------
def doc_type_hint(question: str):
    q = question.lower()
    if _has(r"\b(policy|policies|approve|approval|approver|threshold)\b", q):
        return "policy"
    if _has(r"\binvoice\b", q):
        return "invoice"
    if _has(r"\breport\b", q):
        return "report"
    return None


def docs_node(state: State) -> dict:
    raw = search_documents.invoke({"question": state["question"], "k": 4})
    results = json.loads(raw)
    if isinstance(results, dict):          # {"error": ...}
        return {"tool_output": raw, "top_score": 0.0}

    top_score = max((r["score"] for r in results), default=0.0)
    hint = doc_type_hint(state["question"])
    preferred = [r for r in results if hint and r["document_type"] == hint]
    rest = [r for r in results if r not in preferred]
    kept = (preferred + rest)[:2]
    log.info(f"[docs] hint={hint} kept={[r['source'] for r in kept]} "
             f"top_score={top_score}")
    return {"tool_output": json.dumps(kept, ensure_ascii=False),
            "top_score": top_score}


# ---------------------------------------------------------------
# 3) مسار SQL: النموذج بيكتب SQL، الأداة (للقراءة فقط) بتنفذه
# ---------------------------------------------------------------
SQL_SYSTEM = """You write ONE SQLite SELECT statement and nothing else
(no markdown, no explanation).
Tables/views (quote names with spaces or hyphens using double quotes):
- orders("Order ID","Order Date","Customer Name","Segment","Region","Category",
  "Sub-Category","Product Name","Sales","Quantity","Discount","Profit",order_date_fixed)
- category_group(Category, business_line)
- category_summary(Category,total_sales,total_profit,overall_profit_margin)
- subcategory_summary("Sub-Category",total_sales,total_profit,overall_profit_margin)
- region_summary(Region,total_sales,total_profit,overall_profit_margin)
Prefer the summary views when they answer the question.
Always include the value column(s) you rank or filter by in the SELECT list,
so the answer can state the numbers.
The data covers 2014-01-03 to 2017-12-30. If the question mentions a month
without a year, include the year in the result (GROUP BY year too)."""


def _clean_sql(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:sql)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def sql_node(state: State) -> dict:
    try:
        sql = _clean_sql(llm_text(SQL_SYSTEM, state["question"]))
    except Exception as e:
        log.error(f"[sql] could not generate SQL: {str(e)[:150]}")
        return {"sql": "", "tool_output": json.dumps({"error": "llm_unavailable"})}
    out = query_cost_table.invoke({"sql": sql})
    return {"sql": sql, "tool_output": out}


# ---------------------------------------------------------------
# 4) Validate: نتحقق قبل ما نجاوب
# ---------------------------------------------------------------
def validate(state: State) -> dict:
    try:
        data = json.loads(state.get("tool_output", ""))
    except Exception:
        return {"valid": False, "reason": "tool output is not valid JSON"}

    if state["route"] == "docs":
        if isinstance(data, dict) and "error" in data:
            return {"valid": False, "reason": f"search error: {data['error']}"}
        if state.get("top_score", 0.0) < MIN_DOC_SCORE:
            return {"valid": False,
                    "reason": f"best similarity {state.get('top_score')} < {MIN_DOC_SCORE}"}
        return {"valid": True, "reason": "ok"}

    # sql
    if "error" in data:
        return {"valid": False, "reason": f"sql error: {data['error']}"}
    if not data.get("rows"):
        return {"valid": False, "reason": "query returned no rows"}
    return {"valid": True, "reason": "ok"}


def after_validate(state: State) -> str:
    return "answer" if state["valid"] else "fallback"


# ---------------------------------------------------------------
# 5) Answer + Fallback
# ---------------------------------------------------------------
ANSWER_SYSTEM = """You answer using ONLY the tool output provided.
Be short and direct. Always mention the source: the document name, or the SQL
table/view used. If the tool output does not contain the answer, say exactly:
"I don't have enough information to answer that."
Facts about the data: the sales database covers 2014-01-03 to 2017-12-30; the
documents (invoices, reports, policies) refer to 2024. If you use SQL results,
state the date range they cover. Never present an all-years aggregate as one
specific year."""


def answer_node(state: State) -> dict:
    user = f"Question: {state['question']}\n\nTool output:\n{state['tool_output']}"
    if state["route"] == "sql":
        user += f"\n\nSQL used: {state.get('sql', '')}"
    try:
        return {"answer": llm_text(ANSWER_SYSTEM, user)}
    except Exception as e:
        log.error(f"[answer] all models failed: {str(e)[:150]}")
        return {"answer": "Service unavailable, please try again later.",
                "reason": "llm_unavailable"}


def fallback_node(state: State) -> dict:
    reason = state.get("reason") or "question is outside the available data and documents"
    log.warning(f"[fallback] reason={reason}")
    return {"answer": "I don't have enough information to answer that.",
            "reason": reason}


# ---------------------------------------------------------------
# بناء الـ graph
# ---------------------------------------------------------------
g = StateGraph(State)
g.add_node("classify", classify)
g.add_node("docs", docs_node)
g.add_node("sql", sql_node)
g.add_node("validate", validate)
g.add_node("answer", answer_node)
g.add_node("fallback", fallback_node)

g.add_edge(START, "classify")
g.add_conditional_edges("classify", lambda s: s["route"],
                        {"docs": "docs", "sql": "sql", "fallback": "fallback"})
g.add_edge("docs", "validate")
g.add_edge("sql", "validate")
g.add_conditional_edges("validate", after_validate,
                        {"answer": "answer", "fallback": "fallback"})
g.add_edge("answer", END)
g.add_edge("fallback", END)

app = g.compile()


def ask(question: str) -> dict:
    return app.invoke({"question": question})


if __name__ == "__main__":
    # 3 أسئلة: وثائق (طلب LLM واحد)، SQL (طلبين)، خارج النطاق (صفر طلبات)
    for q in ["What is the discount policy for furniture?",
              "Which region had the highest total sales?",
              "What is the capital of France?"]:
        r = ask(q)
        print(f"\nQ: {q}")
        print(f"route={r['route']} valid={r.get('valid')} reason={r.get('reason')}")
        print("A:", r["answer"])