import json
from unittest.mock import MagicMock, patch

from agent import orchestrator


class MockMessage:
    def __init__(self, content=None, tool_calls=None):
        self.role = "assistant"
        self.content = content
        self.tool_calls = tool_calls or []

    def __getattr__(self, name):
        if name == "tool_call_id":
            return getattr(self, "_tool_call_id", None)
        if name == "name":
            return getattr(self, "_name", None)
        raise AttributeError(name)


def _make_chat_resp(content=None, tool_calls=None):
    msg = MockMessage(content=content, tool_calls=tool_calls)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _tool_call(name, args):
    tc = MagicMock()
    tc.id = "call_1"
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = json.dumps(args)
    return tc


def test_policy_question_triggers_vector_search():
    client = MagicMock()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: LLM decides to search for policy
            return _make_chat_resp(
                tool_calls=[_tool_call("vector_search_hr_policy", {"query": "casual leave allowance"})]
            )
        else:
            # Second call: LLM answers with retrieved policy
            return _make_chat_resp(content="Employees get 12 casual leaves per year.")

    client.chat.completions.create.side_effect = side_effect
    orchestrator.set_client_for_testing(client)
    try:
        result = orchestrator.run_agentic_workflow("How many casual leaves?")
    finally:
        orchestrator.set_client_for_testing(None)
    assert "vector_search_hr_policy" in result["tools"]
    assert result["answer"] != ""
    assert "history" in result


def test_booking_question_skips_vector_search():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_chat_resp(
        tool_calls=[_tool_call("submit_leave_request", {"employee_id": "EMP101", "leave_type": "casual", "start_date": "2026-06-10", "total_days": 2})]
    )
    orchestrator.set_client_for_testing(client)
    try:
        result = orchestrator.run_agentic_workflow("Book casual leave 2026-06-10 for 2 days", employee_id="EMP101")
    finally:
        orchestrator.set_client_for_testing(None)
    assert "submit_leave_request" in result["tools"]
    assert "vector_search_hr_policy" not in result["tools"]


def test_multi_turn_context():
    client = MagicMock()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_chat_resp(
                tool_calls=[_tool_call("vector_search_hr_policy", {"query": "casual leave allowance"})]
            )
        elif call_count == 2:
            return _make_chat_resp(content="You get 12 casual leaves per year.")
        else:
            return _make_chat_resp(content="Your balance is 10 days.")

    client.chat.completions.create.side_effect = side_effect
    orchestrator.set_client_for_testing(client)
    try:
        # First turn
        r1 = orchestrator.run_agentic_workflow("How many casual leaves?", employee_id="EMP101")
        assert "vector_search_hr_policy" in r1["tools"]
        # Second turn with history
        r2 = orchestrator.run_agentic_workflow("What's my balance?", employee_id="EMP101", history=r1["history"])
        assert r2["history"] is not None
        assert len(r2["history"]) > len(r1["history"])
    finally:
        orchestrator.set_client_for_testing(None)
