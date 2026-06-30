from dataclasses import dataclass
from agents import Agent, Runner, function_tool, RunHooks, WebSearchTool, SQLiteSession, RunConfig, SessionSettings
from pydantic import BaseModel
from typing import List
import asyncio
from agents.model_settings import ModelSettings
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio
import os

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_API_KEY")

# async def approval_policy(run_context, agent, tool):
#     return tool.name == "API-post-page"

notion_mcp = MCPServerStdio(
    name="Notion MCP",
    # require_approval=approval_policy, # require GUI to take approval input
    # require_approval={"always": {"tool_names": ["API-post-page"]}},
    params={
        "command": r"C:\Users\rzulf\AppData\Roaming\npm\notion-mcp-server.cmd",
        "env": {
            "NOTION_TOKEN": NOTION_TOKEN,
            "PATH": os.environ.get("PATH", ""),
        }
    },
    client_session_timeout_seconds=30 #Maximum idle time for the client session.
)

# dependency injection tool to be passed to agents (context)
@dataclass
class UserContext:
    name: str
    uid: str
    is_pro_user: bool

class Task(BaseModel):
    taskname: str
    deadline: str
    steps: List[str]
    resources: List[str]

# Output type (Pydantic Model)
class ToDoList(BaseModel):
    tasks: List[Task]

def display_task(todo: ToDoList):
    for task in todo.tasks:
        print(f"Task: {task.taskname}")
        print(f"Deadline: {task.deadline}")
        for i, step in enumerate(task.steps):
            print(f"{i+1}: {step}")
        print("Resources: ")
        for i, src in enumerate(task.resources):
            print(f"{i+1}: {src}")
        print()

display_task_tool = function_tool(display_task)

class LoggingHooks(RunHooks):
    async def on_agent_start(self, context, agent):
        print(f"Starting {agent.name}")

    async def on_llm_end(self, context, agent, response):
        print(f"{agent.name} produced {len(response.output)} output items")

    async def on_agent_end(self, context, agent, output):
        print(f"{agent.name} finished with usage: {context.usage}")

resource_finder_agent = Agent(
    name="Resource Helper",
    instructions="Find and Return helpful resources' links related to user's tasks",
    tools=[WebSearchTool()],
)

extractor_agent = Agent[UserContext](
    name="ToDoList Creator",
    model="gpt-5.4-nano",
    instructions="Extract Task items from student's paragraph. Each Task must have taskname, deadline, 2-4 steps, real resource URLs starting with https://.",
    output_type=ToDoList,
    tools=[display_task_tool],
    handoffs=[resource_finder_agent],
)

notion_agent = Agent[UserContext](
    name="Notion Saver",
    model="gpt-5.4-nano",
    instructions="""You receive tasks in JSON format. For each task:
    1. Search for 'To Do List' page to get its ID
    2. Create a child page with:
       - title = task.taskname  (MUST use taskname field as the page title)
       - content = deadline, steps as bullets, resources as links
    NEVER name a page 'New Page'. Always use the taskname as title.""",
    mcp_servers=[notion_mcp],
    model_settings=ModelSettings(tool_choice="required"),
)

task_retrieval_agent = Agent[UserContext](
    name="Task Retrieval",
    model="gpt-5.4-nano",
    instructions="Retrieve pending tasks from conversation history.",
    output_type=ToDoList,
)

# Create session instance
session = SQLiteSession("conversation_123")

def keep_recent_history(history, new_input):
    # Keep only the last 10 history items, then append the new turn.
    return history[-10:] + new_input

ctx = UserContext(
    name="Rabia",
    uid="123",
    is_pro_user=True
)

async def main():
    streamed = Runner.run_streamed(
        extractor_agent,
        "I have to do 3 tasks this week: finish my discrete maths assignment, practice fighting skills on enemy, and work on my internship task about agents.",
        context=ctx,
        hooks=LoggingHooks(),
        session=session
    )

    async for event in streamed.stream_events():
        if event.type == "agent_updated_stream_event":
            print(f"Current agent: {event.new_agent.name}")

        elif event.type == "run_item_stream_event":
            print(f"Generated item type: {event.item.type}")

    todo: ToDoList = streamed.final_output
    # display_task(todo)

    # Second turn - agent automatically remembers previous context
    # result = await Runner.run(
    #     task_retrieval_agent,
    #     "What are my pending tasks",
    #     context=ctx,
    #     hooks=LoggingHooks(),
    #     session=session,
    #     run_config=RunConfig(
    #       session_settings=SessionSettings(limit=50),
    #       session_input_callback=keep_recent_history
    #     ),
    # )

    # display_task(result.final_output)

    async with notion_mcp:  # ← MCPServerStreamableHttp needs context manager
        notion_result = await Runner.run(
            notion_agent,
            f"Save these tasks to Notion: {todo.model_dump_json()}",
            context=ctx,
            hooks=LoggingHooks(),
        )
        print(notion_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())

