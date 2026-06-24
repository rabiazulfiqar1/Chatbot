from dataclasses import dataclass
from agents import Agent, Runner, function_tool, RunHooks, WebSearchTool
from pydantic import BaseModel
from typing import List
import asyncio
from agents.agent import StopAtTools

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

@function_tool
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
    tools=[display_task],
    handoffs=[resource_finder_agent],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["display_task"])
)

ctx = UserContext(
    name="Rabia",
    uid="123",
    is_pro_user=True
)

async def main():
    await Runner.run(
        agent,
        "I have three different tasks this week: finish my discrete maths assignment, complete a stock prediction research paper report for my FYP, and work on my internship task about agents. I need to organize them separately and submit each on time.",
        context=ctx,
        hooks=LoggingHooks()
    )

if __name__ == "__main__":
    asyncio.run(main())

