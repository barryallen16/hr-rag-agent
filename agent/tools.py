mcp_tools = [
    {
        "type": "function",
        "function": {
            "name": "vector_search_hr_policy",
            "description": "Searches the vector database for HR rules, policies, allowances, leave counts, WFH, holidays. You MUST call this for ANY HR policy or leave question before answering. Example query: 'casual leave allowance per year'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The semantic search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_leave_request",
            "description": "Writes a new leave application to the SQL database. Call ONLY when the user explicitly asks to book/apply/deduct leave and provides leave_type, start_date, and total_days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "leave_type": {"type": "string", "enum": ["medical", "casual"]},
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD"},
                    "total_days": {"type": "integer"}
                },
                "required": ["employee_id", "leave_type", "start_date", "total_days"]
            }
        }
    }
]