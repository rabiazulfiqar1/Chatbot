import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

history = []

def generate_response(query):
    history.append({
        "role": "user",
        "content": query
    })
    completion = client.chat.completions.create(
        model="gpt-5.4",
        messages=[
            {"role": "system", "content": "Talk like a pirate."},
            *history
        ],
    )

    return completion.choices[0].message.content

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


