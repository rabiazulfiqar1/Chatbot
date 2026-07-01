import datetime

# These get sent to OpenAI as part of the session config so the model
# knows what it's allowed to call. Keeping this on the backend means
# YOU control what the agent can touch -- the browser never sees this list
# being editable, it just relays call requests.
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Get the current date and time.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "leetcode_streak",
        "description": "Return the user's current LeetCode streak stats.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]


def execute_tool(name: str, arguments: dict) -> dict:
    """
    This is where account permissions, logging, and budgets would live.
    Add your own checks here before actually running anything real
    (e.g. rate-limit per user, log every call, block tools per-session).
    """
    if name == "get_current_time":
        return {"now": datetime.datetime.now().isoformat()}

    if name == "leetcode_streak":
        return {"streak_days": 40, "problems_solved": 186}

    return {"error": f"unknown tool: {name}"}
