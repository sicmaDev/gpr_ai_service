import json
from pathlib import Path

audit_path = Path("audit_data_workflow_20261016_234714.json")
data = json.loads(audit_path.read_text(encoding="utf-8"))

for r in data.get("runs", []):
    rid = r.get("run_id")
    if rid in [5, 7, 10, 19, 21, 23]:
        print(f"=== RUN {rid} : {r.get('question')} ===")
        print("Routing:", r.get("routing"))
        print("Query ID:", r.get("final_qid"))
        sql = r.get("sql_executed") or r.get("step4_candidate_sql", {}).get("candidate_sql")
        print("SQL:", sql)
        print("Synthesis:", r.get("step7_restitution", {}).get("synthesis"))
        print()
