import json
import logging

from openai import OpenAI

from agent.tools import mcp_tools
from config import API_KEY, LLM_BASE_URL, MODEL_NAME
from database.relational import submit_leave_request
from database.vector import vector_search_hr_policy

log = logging.getLogger(__name__)
client = OpenAI(base_url=LLM_BASE_URL, api_key=API_KEY)

MAX_ITERS = 5


def run_agentic_workflow(user_prompt, employee_id="EMP123", history=None):
    messages = [{"role": "system", "content": f"You are an enterprise HR automation agent. Employee ID: {employee_id}. Dates YYYY-MM-DD. Rules: For ANY HR policy question, you MUST call vector_search_hr_policy before answering; never answer policy questions from memory. Never state a policy fact without first calling vector_search_hr_policy. Never call submit_leave_request for policy questions. Example: 'How many casual leaves per year?' -> call vector_search_hr_policy with query 'casual leave allowance per year'. Only call submit_leave_request when the user explicitly asks to book/apply/deduct leave AND provides leave type, start date, and days. Never invent dates or employee IDs. If required info is missing, ask the user instead of guessing."}]
    tools_called = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})
    print(f"\n--- User Query ---\n{user_prompt}")

    policy_kw = ["policy", "doctor", "how many", "wfh", "work from home", "maternity", "paternity", "holiday", "allowance", "rule", "note"]
    force_policy = False

    for i in range(MAX_ITERS):
        tc = "auto"
        if i == 0 and force_policy:
            tc = "required"
        try:
            resp = client.chat.completions.create(model=MODEL_NAME, messages=messages, tools=mcp_tools, tool_choice=tc)
        except Exception as e:
            log.exception("LLM call failed")
            print(f"LLM error: {e}")
            return {"tools": tools_called, "answer": ""}
        msg = resp.choices[0].message
        if not msg.tool_calls:
            print(f"--- Final Agent Response ---\n{msg.content}")
            return {"tools": tools_called, "answer": msg.content or ""}
        messages.append(msg)
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            print(f"[Executing Tool] -> {name} {args}")
            if name == "vector_search_hr_policy":
                tools_called.append(name)
                result = vector_search_hr_policy(args.get("query", ""))
            elif name == "submit_leave_request":
                import re
                booking_kw = any(k in user_prompt.lower() for k in ["book", "apply", "deduct", "request", "take"])
                has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}", user_prompt))
                if not (booking_kw and has_date):
                    result = json.dumps({"status": "error", "message": "Not an explicit booking request; ask user for details."})
                    messages.append({"role": "tool", "tool_call_id": tc.id, "name": name, "content": str(result)})
                    print(f"[System Execution Result] -> {result}\n")
                    continue
                tools_called.append(name)
                result = submit_leave_request(
                    employee_id=args.get("employee_id", employee_id),
                    leave_type=args.get("leave_type"),
                    start_date=args.get("start_date"),
                    total_days=args.get("total_days"),
                )
            else:
                tools_called.append(name)
                result = json.dumps({"status": "error", "message": f"unknown tool {name}"})
            print(f"[System Execution Result] -> {result}\n")
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": name, "content": str(result)})
    print("Max iterations reached.")
    return {"tools": tools_called, "answer": ""}