# main.py
from fastapi import FastAPI, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.learning_microsoft_agent_framework.factory import Agent
import os
import asyncio
import json
import uuid
from typing import Optional, AsyncGenerator
from datetime import datetime, UTC

# AG UI Protocol imports
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
)

app = FastAPI()

# AG UI Protocol Models
class ChatRequest(BaseModel):
    user_id: str = "default"
    message: str
    thread_id: Optional[str] = None
    run_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str

# Initialize agent using factory
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
agent_factory = Agent(
    name="MyReactChatAgent",
    model=MODEL_NAME,
    instructions="You are a helpful assistant for a website chat interface.",
    tools=[]
)

# WebSocket endpoint for real-time chat with AG UI Protocol
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    thread_id = str(uuid.uuid4())
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                user_id = message_data.get("user_id", "default")
                run_id = str(uuid.uuid4())
                
                if not user_message:
                    error_event = RunErrorEvent(
                        type=EventType.RUN_ERROR,
                        message="No message provided",
                        timestamp=int(datetime.now(UTC).timestamp() * 1000)
                    )
                    await websocket.send_text(error_event.model_dump_json())
                    continue
                
                # Use factory's run method which yields all AG UI events
                async for event in agent_factory.run(
                    message=user_message,
                    user_id=user_id,
                    thread_id=thread_id,
                    run_id=run_id
                ):
                    await websocket.send_text(event.model_dump_json())
                
            except json.JSONDecodeError:
                error_event = RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    message="Invalid JSON format",
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(error_event.model_dump_json())
            except Exception as e:
                error_event = RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    message=str(e),
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(error_event.model_dump_json())
                
    except WebSocketDisconnect:
        print(f"Client disconnected from thread {thread_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)