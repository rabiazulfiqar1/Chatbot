import asyncio
from agents import Agent, Runner, function_tool

# function tools
@function_tool
def history_fun_fact() -> str:
    """Return a short history fact."""
    return "Sharks are older than trees."

# agent as tools
history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You answer history questions clearly and concisely.",
)

math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You explain math step by step and include worked examples.",
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route each homework question to the right specialist.",
    handoffs=[history_tutor_agent, math_tutor_agent],
)

# agent = Agent(
#     name="History Tutor",
#     instructions="Answer history questions clearly. Use history_fun_fact when it helps.",
#     tools=[history_fun_fact],
# )

async def main():
    # result = await Runner.run(
    #     agent,
    #     "Tell me something surprising about ancient life on Earth.",
    # )
    # print(result.final_output)
    result = await Runner.run(
        triage_agent,
        "Who was the first president of the United States?",
    )
    print(result.final_output)
    print(f"Answered by: {result.last_agent.name}")


if __name__ == "__main__":
    asyncio.run(main())

