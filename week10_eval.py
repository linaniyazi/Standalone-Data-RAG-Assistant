import csv
import os
import sys
import time

from week10_agent import ask_with_trace

# (السؤال، الأداة المتوقعة أو None، كلمة لازم تظهر بالجواب)
QUESTIONS = [
    ("What is the discount policy for furniture?", "search_documents", "5%"),
    ("How much was the total invoice amount?", "search_documents", "2,097.45"),
    ("Which region performed best in October?", "search_documents|query_cost_table", "West"),
    ("What happens if a payment is late?", "search_documents", "2%"),
    ("How long does it take to process a new order?", "search_documents", "2-3"),
    ("What payment methods are accepted?", "search_documents", "bank transfer"),
    ("What discount was applied to the November invoice?", "search_documents", "10%"),
    ("Which sub-category had a negative profit margin?", "query_cost_table", "Tables"),
    ("Who needs to approve a 15% discount?", "search_documents", "Regional Sales Manager"),
    ("What is the capital of France?", None, "enough information"),
]

OUT = "eval_results.csv"
FIELDS = ["n", "question", "expected_tool", "tools_used", "tool_ok",
        "keyword", "keyword_ok", "auto_pass", "model", "steps",
        "seconds", "answer", "manual_review"]


def main():
    # الاستخدام: python week10_eval.py 0 4   (بيشغل الأسئلة 1 إلى 4)
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    new_file = not os.path.exists(OUT)

    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()

        for i in range(lo, min(hi, len(QUESTIONS))):
            q, exp_tool, kw = QUESTIONS[i]
            r = ask_with_trace(q)
            if exp_tool is None:
                tool_ok = len(r["tools_used"]) == 0
            else:
                tool_ok = any(t in r["tools_used"] for t in exp_tool.split("|"))
            kw_ok = kw.lower() in r["answer"].lower()
            row = {
                "n": i + 1, "question": q, "expected_tool": exp_tool or "none",
                "tools_used": "+".join(r["tools_used"]) or "none",
                "tool_ok": tool_ok, "keyword": kw, "keyword_ok": kw_ok,
                "auto_pass": tool_ok and kw_ok, "model": r["model"],
                "steps": r["steps"], "seconds": r["seconds"],
                "answer": r["answer"].replace("\n", " "), "manual_review": "",
            }
            w.writerow(row)
            f.flush()
            print(f"[{i+1}] tool_ok={tool_ok} keyword_ok={kw_ok} "
                f"model={r['model']} -> {q}")
            time.sleep(2)


if __name__ == "__main__":
    main()