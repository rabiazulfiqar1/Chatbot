import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from openai import AsyncOpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=2, # configurable
    timeout=10.0, # configurable
)

asyncClient = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=2, # configurable
    timeout=10.0, # configurable
)

history = []

async def generate_async_response(query):
    history.append({
        "role": "user",
        "content": query
    })

    try:
        stream = await asyncClient.responses.create(
            model="gpt-4o-mini",
            instructions="Talk in a frinedly way.",
            input=history,
            stream=True
        )
    except openai.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
        return ""
    except openai.RateLimitError:
        print("A 429 status code was received; we should back off a bit.")
        return ""
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)
        return ""

    # stream = await asyncClient.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": "Talk in a frinedly way."},
    #         *history
    #     ],
    #     stream = True
    # )

    response =""
    async for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
            response += event.delta
            
        # if event.choices[0].delta.content:
        #     print(event.choices[0].delta.content, end="", flush=True)
        #     response += event.choices[0].delta.content
    
    print()
    return response


def generate_response(query):
    history.append({
        "role": "user",
        "content": query
    })
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Talk in a frinedly way."},
                *history
            ],
            stream = True
        )
    except openai.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
        return ""
    except openai.RateLimitError:
        print("A 429 status code was received; we should back off a bit.")
        return ""
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)
        return ""


    response = ""
    for event in stream:
        if event.choices[0].delta.content:
            print(event.choices[0].delta.content, end="", flush=True)
            response += event.choices[0].delta.content

    print()
    return response

async def main():
    while True:
        user_query = input("Enter prompt Or q to exit: ")
        if (user_query == "q"):
            break
        response = await generate_async_response(user_query)
        history.append({
            "role": "assistant",
            "content": response
        })
        print(history)

asyncio.run(main())
