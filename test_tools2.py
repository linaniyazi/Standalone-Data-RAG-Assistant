''' from week10_tools import search_documents

for q in ["What is the discount policy for furniture?",
        "What happens if a payment is late?",
        "Who needs to approve a 15% discount?"]:
        out = search_documents.invoke({"question": q, "k": 1})
        print(q, "->", out[:120], "\n") '''
'''      
        
from week10_tools import query_cost_table

tests = [
'SELECT Region, total_sales FROM region_summary ORDER BY total_sales DESC',
'SELECT "Sub-Category", overall_profit_margin FROM subcategory_summary ORDER BY overall_profit_margin LIMIT 3',
'DROP TABLE orders',
'SELECT * FROM orders; DELETE FROM orders',
]
for t in tests:
        print(t, "\n ->", query_cost_table.invoke({"sql": t})[:150], "\n")
        '''
        
        
import json
from week10_tools import summarize_result

out = summarize_result.invoke({"text": "West: 725,457 sales. East: 678,781. Central: 501,239. South: 391,721."})
print(out)