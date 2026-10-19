import argparse

from agent.orchestrator import run_agentic_workflow
from database.relational import init_relational_db
from database.vector import init_vector_db


def setup():
    print("Initializing Enterprise Infrastructure...")
    init_relational_db()
    init_vector_db()
    print("System Ready.\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--employee-id", default="EMP123")
    parser.add_argument("query", nargs="*")
    args = parser.parse_args()
    setup()
    if args.query:
        run_agentic_workflow(" ".join(args.query), employee_id=args.employee_id)
        return
    print("Interactive mode. Type 'exit' to quit.")
    while True:
        q = input("> ").strip()
        if not q or q.lower() in {"exit", "quit"}:
            break
        run_agentic_workflow(q, employee_id=args.employee_id)

if __name__ == "__main__":
    main()