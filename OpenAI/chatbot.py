import os
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from openai import AsyncOpenAI #noqa

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

asyncClient = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

history = []

async def generate_async_response(query):
    history.append({
        "role": "user",
        "content": query
    })
    stream = await asyncClient.chat.completions.create(
        model="gpt-5.4",
        messages=[
            {"role": "system", "content": "Talk like a pirate."},
            *history
        ],
        stream = True
    )

    response =""
    async for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
            response += event.delta
    
    print()
    return response


def generate_response(query):
    history.append({
        "role": "user",
        "content": query
    })
    stream = client.chat.completions.create(
        model="gpt-5.4",
        messages=[
            {"role": "system", "content": "Talk like a pirate."},
            *history
        ],
        stream = True
    )

    response = ""
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
            response += event.delta

    print()
    return response

async def main():
    while True:
        user_query = input("Enter prompt Or q to exit: ")
        if (user_query == "q"):
            break
        response = generate_response(user_query)
        history.append({
            "role": "assistant",
            "content": response
        })
        print(history)

asyncio.run(main)


