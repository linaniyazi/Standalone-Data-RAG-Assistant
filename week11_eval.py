import csv
import os
import sys
import time

from week11_graph import ask

# (السؤال، المسار المتوقع، كلمة لازم تظهر بالجواب)
QUESTIONS = [
    ("What is the discount policy for furniture?", "docs", "5%"),
    ("How much was the total invoice amount?", "docs", "2,097.45"),
    ("Which region performed best in October?", "sql", "2014"),   # بنفحص إنو ذكر الفترة
    ("What happens if a payment is late?", "docs", "2%"),
    ("How long does it take to process a new order?", "docs", "business days"),
    ("What payment methods are accepted?", "docs", "bank transfer"),
    ("What discount was applied to the November invoice?", "docs", "10%"),
    ("Which sub-category had a negative profit margin?", "sql", "Tables"),
    ("Who needs to approve a 15% discount?", "docs", "Regional Sales Manager"),
    ("What is the capital of France?", "fallback", "enough information"),
]

OUT = "eval_results_week11.csv"
FIELDS = ["n", "question", "expected_route", "route", "route_ok", "valid",
          "reason", "keyword", "keyword_ok", "auto_pass", "seconds",
          "answer", "manual_review"]


def norm(text: str) -> str:
    return text.replace("–", "-").replace("—", "-").lower()


def main():
    # الاستخدام: python week11_eval.py 0 5   (الأسئلة 1 إلى 5)
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    new_file = not os.path.exists(OUT)

    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for i in range(lo, min(hi, len(QUESTIONS))):
            q, exp_route, kw = QUESTIONS[i]
            start = time.time()
            r = ask(q)
            secs = round(time.time() - start, 1)
            route_ok = r["route"] == exp_route
            kw_ok = norm(kw) in norm(r["answer"])
            w.writerow({
                "n": i + 1, "question": q, "expected_route": exp_route,
                "route": r["route"], "route_ok": route_ok,
                "valid": r.get("valid", ""), "reason": r.get("reason", ""),
                "keyword": kw, "keyword_ok": kw_ok,
                "auto_pass": route_ok and kw_ok, "seconds": secs,
                "answer": r["answer"].replace("\n", " "), "manual_review": "",
            })
            f.flush()
            print(f"[{i+1}] route_ok={route_ok} keyword_ok={kw_ok} "
                  f"{secs}s -> {q}")
            time.sleep(2)


if __name__ == "__main__":
    main()