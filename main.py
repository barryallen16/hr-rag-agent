from database.relational import init_relational_db
from database.vector import init_vector_db
from agent.orchestrator import run_agentic_workflow

def setup():
    """Initialize databases before running the agent."""
    print("Initializing Enterprise Infrastructure...")
    init_relational_db()
    init_vector_db()
    print("System Ready.\n")

if __name__ == "__main__":
    setup()
    
    run_agentic_workflow("Do I need to submit a doctor's note for a 3-day sick leave?", employee_id="EMP123")
    
    run_agentic_workflow("Please deduct 2 days of casual leave starting 2026-06-10.", employee_id="EMP123")