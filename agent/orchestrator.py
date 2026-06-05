import json
from openai import OpenAI
from config import LLM_BASE_URL, API_KEY, MODEL_NAME
from database.relational import submit_leave_request
from database.vector import vector_search_hr_policy
from agent.tools import mcp_tools

client = OpenAI(base_url=LLM_BASE_URL, api_key=API_KEY, default_headers={"ngrok-skip-browser-warning": "true"})

def run_agentic_workflow(user_prompt: str, employee_id: str = "EMP123"):
    print(f"\n--- User Query ---\n{user_prompt}")
    
    messages = [
        {"role": "system", "content": f"You are an enterprise HR automation agent routing to actual database systems. Current employee context: ID is {employee_id}. Ensure start_date is formatted as YYYY-MM-DD."},
        {"role": "user", "content": user_prompt}
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=mcp_tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    if response_message.tool_calls:
        messages.append(response_message) 
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"[Executing Tool] -> {function_name}")
            print(f"[Extracted Args] -> {arguments}")
            
            if function_name == "vector_search_hr_policy":
                result = vector_search_hr_policy(arguments.get("query"))
            elif function_name == "submit_leave_request":
                result = submit_leave_request(
                    employee_id=arguments.get("employee_id", employee_id),
                    leave_type=arguments.get("leave_type"),
                    start_date=arguments.get("start_date"),
                    total_days=arguments.get("total_days")
                )
            
            print(f"[System Execution Result] -> {result}\n")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(result)
            })
        
        final_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        print(f"--- Final Agent Response ---\n{final_response.choices[0].message.content}")
    else:
        print(f"--- Final Agent Response ---\n{response_message.content}")