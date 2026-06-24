from dataclasses import dataclass
from agents import Agent, Runner, function_tool
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

# Output type (Pydantic Model)
class ToDoList(BaseModel):
    tasks: List[Task]

@function_tool
def display_task(task: Task):
    print(f"Task: {task.taskname}")
    print(f"Deadline: {task.deadline}")
    for i, step in enumerate(task.steps):
        print(f"{i+1}: {step}")
    print()

agent = Agent[UserContext](
    name="ToDoList Creator",
    model="gpt-5.4-nano",
    instructions="Read the student's paragraph and extract multiple tasks with deadlines and short steps and lastly display tasks. Use tool if needed",
    output_type=ToDoList,
    tools=[display_task]
)

ctx = UserContext(
    name="Rabia",
    uid="123",
    is_pro_user=True
)

async def main():
    result = await Runner.run(
        agent,
        "I have three tasks for my CS assignment: write the code, test it with sample inputs, and prepare a short report. I also need to add screenshots and submit everything by Friday evening.",
        context=ctx
    )
    # todo = result.final_output
    # for task in todo.tasks:
    #     display_task(task)

if __name__ == "__main__":
    asyncio.run(main())

