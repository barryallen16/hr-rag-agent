import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
tmp = Path(tempfile.mkdtemp())
os.environ["SQL_DB_PATH"] = str(tmp / "t.db")
os.environ["VECTOR_DB_PATH"] = str(tmp / "chroma")
os.environ["EMPLOYEES_CSV_PATH"] = str(ROOT / "data" / "employees.csv")
os.environ["POLICIES_CSV_PATH"] = str(ROOT / "data" / "hr_policies.csv")

from agent.orchestrator import run_agentic_workflow
from database.relational import init_relational_db
from database.vector import init_vector_db
from eval.cases import CASES

init_relational_db()
init_vector_db()

results = []
tool_ok = 0
for c in CASES:
    r = run_agentic_workflow(c["query"], employee_id=c["employee_id"])
    actual = r.get("tools", [])
    ans = (r.get("answer") or "").lower()
    tm = set(actual) == set(c["expected_tools"])
    am = all(k.lower() in ans for k in c["answer_contains"])
    if tm:
        tool_ok += 1
    results.append({"id": c["id"], "tools": actual, "tool_match": tm, "answer_match": am})
    print(f"{c['id']}: tools={actual} tool_match={tm} answer_match={am}")

print(f"\nTool accuracy: {tool_ok}/{len(CASES)} = {100 * tool_ok / len(CASES):.1f}%")
Path("eval/results.json").write_text(json.dumps(results, indent=2))