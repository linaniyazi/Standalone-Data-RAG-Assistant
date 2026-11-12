"""Entry point of the Data + RAG Assistant.

python app.py                      -> interactive mode
python app.py "your question"      -> one question
python app.py --demo               -> run the demo questions
python app.py --clean              -> run the ETL (clean the Retail Store Sales data)
python app.py --rebuild            -> rebuild superstore.db from data/Superstore.csv
python app.py --chunks             -> rebuild chunks.json from documents/*.txt
"""
import json
import sys
import warnings

warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")

try:
    from dotenv import load_dotenv
    load_dotenv()          # يقرأ GEMINI_API_KEY من ملف .env إذا موجود
except ImportError:
    pass

DEMO_QUESTIONS = [
    "What is the discount policy for furniture?",
    "How much was the total invoice amount?",
    "Which region performed best in October?",
    "What happens if a payment is late?",
    "How long does it take to process a new order?",
    "What payment methods are accepted?",
    "What discount was applied to the November invoice?",
    "Which sub-category had a negative profit margin?",
    "Who needs to approve a 15% discount?",
    "Which category has the highest overall profit margin?",
    "What about it?",                         # سؤال غامض
    "What is the capital of France?",         # خارج النطاق
]


def build_response(state: dict) -> dict:
    """Turn the graph state into a clean answer + the evidence used."""
    route = state.get("route")
    sources, sql = [], None
    if route == "docs":
        try:
            sources = sorted({c["source"] for c in json.loads(state["tool_output"])})
        except Exception:
            sources = []
    elif route == "sql":
        sql = state.get("sql") or None
    return {
        "question": state.get("question"),
        "route": route,
        "valid": state.get("valid"),
        "reason": state.get("reason"),
        "sql": sql,
        "sources": sources,
        "answer": state.get("answer"),
    }


def ask(question: str) -> dict:
    from week11_graph import ask as graph_ask     # import كسول: ما بيحتاج chunks لـ --rebuild
    return build_response(graph_ask(question))


def show(r: dict) -> None:
    print(f"\nQ: {r['question']}")
    print(f"   route: {r['route']}" + (f" (invalid: {r['reason']})" if r["valid"] is False else ""))
    if r["sql"]:
        print(f"   SQL:   {r['sql']}")
    if r["sources"]:
        print(f"   retrieved: {', '.join(r['sources'])}")
    print(f"A: {r['answer']}")


def rebuild_db() -> None:
    from build_database import build
    build("data/Superstore.csv", "superstore.db")


DOC_TYPES = {
    "faq_orders_payment.txt": "faq",
    "invoice_nov2024.txt": "invoice",
    "policy_discount_approval.txt": "policy",
    "report_october2024.txt": "report",
}


def rebuild_chunks() -> None:
    from chunking_functions import build_document_chunks
    chunks = build_document_chunks("documents", DOC_TYPES)
    chunks.sort(key=lambda c: (c["source_document"], c["chunk_index"]))   # ترتيب ثابت
    with open("chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Wrote chunks.json with {len(chunks)} chunks "
          f"from {len({c['source_document'] for c in chunks})} documents")


def run_cleaning() -> None:
    import logging
    from etl_pipeline import run_pipeline
    root = logging.getLogger()
    already = any(isinstance(h, logging.FileHandler)
                  and h.baseFilename.endswith("etl_pipeline.log") for h in root.handlers)
    if not already:                                # حتى لو تهيّأ الـ logging من وحدة تانية
        root.addHandler(logging.FileHandler("etl_pipeline.log", encoding="utf-8"))
    run_pipeline("data/retail_store_sales.csv", "data/retail_store_sales_cleaned.csv")


def main(argv):
    if "--rebuild" in argv:
        rebuild_db()
    elif "--chunks" in argv:
        rebuild_chunks()
    elif "--clean" in argv:
        run_cleaning()
    elif "--demo" in argv:
        for q in DEMO_QUESTIONS:
            show(ask(q))
    elif len(argv) > 1:
        show(ask(" ".join(argv[1:])))
    else:
        print("Ask a question (empty line to quit).")
        while True:
            q = input("\n> ").strip()
            if not q:
                break
            show(ask(q))


if __name__ == "__main__":
    main(sys.argv)
