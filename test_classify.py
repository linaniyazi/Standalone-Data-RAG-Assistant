# اختبار الـ classifier فقط: بدون Gemini وبدون أي كوتا
from week11_graph import classify_question

CASES = [
    ("What is the discount policy for furniture?", "docs"),
    ("How much was the total invoice amount?", "docs"),
    ("Which region performed best in October?", "sql"),
    ("What happens if a payment is late?", "docs"),
    ("How long does it take to process a new order?", "docs"),
    ("What payment methods are accepted?", "docs"),
    ("What discount was applied to the November invoice?", "docs"),
    ("Which sub-category had a negative profit margin?", "sql"),
    ("Who needs to approve a 15% discount?", "docs"),
    ("What is the capital of France?", "fallback"),
    ("Which region had the highest total sales?", "sql"),
]

ok = 0
for q, expected in CASES:
    got = classify_question(q)
    flag = "OK  " if got == expected else "FAIL"
    ok += got == expected
    print(f"{flag} expected={expected:8} got={got:8} | {q}")
print(f"\n{ok}/{len(CASES)} correct")