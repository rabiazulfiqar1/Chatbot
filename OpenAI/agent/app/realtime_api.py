import asyncio

from agents.realtime import RealtimeAgent, RealtimeRunner
import wave

agent = RealtimeAgent(
    name="Assistant",
    instructions="You are a helpful voice assistant. Keep responses short and conversational.",
)

session_audio = bytearray()

runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "model_name": "gpt-realtime-2",
            "audio": {
                "input": {
                    "format": "pcm16",
                    "transcription": {"model": "gpt-4o-mini-transcribe"},
                    "turn_detection": {
                        "type": "semantic_vad",
                        "interrupt_response": True,
                    },
                },
                "output": {
                    "format": "pcm16",
                    "voice": "ash",
                },
            },
        }
    },
)

async def main() -> None:
    session = await runner.run()

    async with session:

        while True:
            user_msg = input("\nYou: ")

            if user_msg.lower() in ["exit", "quit"]:
                break

            await session.send_message(user_msg)

            audio_chunks = bytearray()

            async for event in session:
                if event.type == "audio":
                    audio_chunks.extend(event.audio.data)
                    # pass
                elif event.type == "history_added":
                    print(event.item)
                elif event.type == "agent_end":
                    session_audio.extend(audio_chunks)
                    break
                elif event.type == "error":
                    # print(f"Error: {event.error}")
                    pass
                elif event.type == "history_updated":
                    history = event.history

                    if history:   
                        last_item = history[-1]

                        if last_item.role == "assistant":
                            for part in last_item.content:
                                if hasattr(part, "transcript") and part.transcript:
                                    print("Assistant:", part.transcript)


if __name__ == "__main__":
    asyncio.run(main())

    with wave.open("response.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)      # PCM16 = 2 bytes
        wf.setframerate(24000)  # default output sample rate, 24 kHz
        wf.writeframes(session_audio)

    print("Saved response.wav")