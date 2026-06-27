from dataclasses import dataclass
from agents import Agent, Runner, function_tool, RunHooks, WebSearchTool, SQLiteSession
from pydantic import BaseModel
from typing import List
import asyncio

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

agent = Agent[UserContext](
    name="ToDoList Creator",
    model="gpt-5.4-nano",
    instructions="Read the student's paragraph and extract Task items. Do not merge different tasks into one item. Each Task must have a short taskname, a deadline, 2 to 4 steps, and real resource URLs starting with https://. Lastly display tasks. Use tools if needed",
    output_type=ToDoList,
    tools=[display_task_tool],
    handoffs=[resource_finder_agent],
)

task_retrieval_agent = Agent[UserContext](
    name="Task Retrieval",
    model="gpt-5.4-nano",
    instructions="Retrieve pending tasks from conversation history.",
    output_type=ToDoList,
)

# Create session instance
session = SQLiteSession("conversation_123")

ctx = UserContext(
    name="Rabia",
    uid="123",
    is_pro_user=True
)

async def main():
    result = Runner.run_streamed(
        agent,
        "I have to do 3 tasks this week: finish my discrete maths assignment, practice fighting skills on enemy, and work on my internship task about agents.",
        context=ctx,
        hooks=LoggingHooks(),
        session=session
    )

    async for event in result.stream_events():
        if event.type == "agent_updated_stream_event":
            print(f"Current agent: {event.new_agent.name}")

        elif event.type == "run_item_stream_event":
            print(f"Generated item type: {event.item.type}")

    # Second turn - agent automatically remembers previous context
    result = await Runner.run(
        task_retrieval_agent,
        "What are my pending tasks",
        context=ctx,
        hooks=LoggingHooks(),
        session=session
    )

    display_task(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())

