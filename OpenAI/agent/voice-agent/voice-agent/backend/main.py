import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools import TOOL_DEFINITIONS, execute_tool

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Copy .env.example to .env and fill it in.")

app = FastAPI()

# Only allow your own frontend origin to call this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend's actual origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is the ONLY place your real API key is used. It never leaves the backend.
SESSION_CONFIG = {
    "session": {
        "type": "realtime",
        "model": "gpt-realtime-2",
        "instructions": (
            "You are a helpful voice assistant. Keep responses short and "
            "conversational. Use tools when the user asks for something "
            "that needs a tool call."
        ),
        "audio": {
            "input": {
                "format": {"type": "audio/pcm", "rate": 24000},
                "transcription": {"model": "gpt-4o-mini-transcribe"},
                "turn_detection": {
                    "type": "semantic_vad",
                    "interrupt_response": True,
                },
            },
            "output": {
                "format": {"type": "audio/pcm", "rate": 24000},
                "voice": "marin",
            },
        },
        "tools": TOOL_DEFINITIONS,
    }
}


@app.get("/token")
async def get_token():
    """
    Browser calls this first. We use our real API key here (server-side only)
    to mint a short-lived ephemeral key ("client secret") that's safe to hand
    to the browser. The browser uses THAT to talk to OpenAI directly.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/realtime/client_secrets",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
                # Replace with a real hashed user id in production.
                # This binds the safety identifier to the token server-side,
                # so the browser never needs to know or send it.
                "OpenAI-Safety-Identifier": "demo-user-hash",
            },
            json=SESSION_CONFIG,
        )

    if resp.status_code != 200:
        print("OpenAI /client_secrets error:", resp.status_code, resp.text)
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


@app.post("/tools/execute")
async def tools_execute(req: ToolCallRequest):
    """
    Browser forwards function-call events here instead of running them
    itself. This is where your account permissions, logging policy, and
    budgets actually live -- exactly like your diagram says.
    """
    result = execute_tool(req.name, req.arguments)
    return {"result": result}


@app.get("/")
def health():
    return {"status": "ok"}