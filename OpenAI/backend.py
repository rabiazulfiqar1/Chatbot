from fastapi import FastAPI
from pydantic import BaseModel

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

app = FastAPI()

class ChatRequest(BaseModel):
    query: str

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

@app.post("/chat")
def chat(req: ChatRequest):
    response = generate_response(req.query)
    history.append({
        "role": "assistant",
        "content": response
    })
    
    return {"response": response}

@app.get("/history")
def getHistory():
    return history

@app.delete("/history")
def delete_history():
    history.clear()
    return {"message": "History deleted successfully"}
