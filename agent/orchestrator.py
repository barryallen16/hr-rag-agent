import json
import logging
from contextlib import contextmanager
import sqlite3
from config import SQL_DB_PATH

from openai import OpenAI

from agent.tools import mcp_tools
from config import API_KEY, LLM_BASE_URL, MODEL_NAME
from database.relational import submit_leave_request
from database.vector import vector_search_hr_policy

log = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=API_KEY)
    return _client


def set_client_for_testing(client):
    """Allow tests to inject a mock client."""
    global _client
    _client = client


@contextmanager
def _session_conn():
    conn = sqlite3.connect(SQL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_sessions_table():
    with _session_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                emp_id TEXT PRIMARY KEY,
                history TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _load_history(employee_id: str):
    _init_sessions_table()
    with _session_conn() as conn:
        row = conn.execute("SELECT history FROM sessions WHERE emp_id=?", (employee_id,)).fetchone()
        if row:
            import json
            return json.loads(row["history"])
    return []


def _save_history(employee_id: str, history):
    _init_sessions_table()
    import json
    with _session_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (emp_id, history, updated_at) VALUES (?,?,datetime('now'))",
            (employee_id, json.dumps(history)),
        )


MAX_ITERS = 5
SYSTEM_PROMPT = "You are an enterprise HR automation agent. Employee ID: {employee_id}. Dates YYYY-MM-DD. Rules: For ANY HR policy question, you MUST call vector_search_hr_policy before answering; never answer policy questions from memory. Never state a policy fact without first calling vector_search_hr_policy. Never call submit_leave_request for policy questions. Example: 'How many casual leaves per year?' -> call vector_search_hr_policy with query 'casual leave allowance per year'. Only call submit_leave_request when the user explicitly asks to book/apply/deduct leave AND provides leave type, start date, and days. Never invent dates or employee IDs. If required info is missing, ask the user instead of guessing."


def _msg_to_dict(msg):
    """Convert OpenAI message object to serializable dict."""
    if isinstance(msg, dict):
        return msg
    d = {"role": msg.role}
    if msg.content is not None:
        d["content"] = msg.content
    if msg.tool_calls:
        d["tool_calls"] = [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]
    if getattr(msg, "tool_call_id", None):
        d["tool_call_id"] = msg.tool_call_id
        d["name"] = msg.name
    return d


def run_agentic_workflow(user_prompt, employee_id="EMP123", history=None):
    if history is None:
        history = _load_history(employee_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(employee_id=employee_id)}]
    tools_called = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})
    log.info("User query: %s", user_prompt)

    for i in range(MAX_ITERS):
        tc = "auto"
        try:
            resp = _get_client().chat.completions.create(model=MODEL_NAME, messages=messages, tools=mcp_tools, tool_choice=tc)
        except Exception as e:
            log.exception("LLM call failed")
            serializable = [_msg_to_dict(m) for m in messages[1:]]
            _save_history(employee_id, serializable)
            return {"tools": tools_called, "answer": "", "history": serializable}
        msg = resp.choices[0].message
        if not msg.tool_calls:
            log.info("Final agent response: %s", msg.content)
            serializable = [_msg_to_dict(m) for m in messages[1:]]
            _save_history(employee_id, serializable)
            return {"tools": tools_called, "answer": msg.content or "", "history": serializable}
        messages.append(_msg_to_dict(msg))
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            log.debug("Executing tool: %s %s", name, args)
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
                    log.debug("Tool result: %s", result)
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
            log.debug("Tool result: %s", result)
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": name, "content": str(result)})
    log.warning("Max iterations reached")
    serializable = [_msg_to_dict(m) for m in messages[1:]]
    _save_history(employee_id, serializable)
    return {"tools": tools_called, "answer": "", "history": serializable}