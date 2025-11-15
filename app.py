# main.py
from fastapi import FastAPI, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent_framework.openai import OpenAIChatClient
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

# Initialize agent once (for simplicity)
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # example
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

chat_client = OpenAIChatClient(
    api_key=OPENAI_API_KEY,
    model_id=MODEL_NAME
)

agent = chat_client.create_agent(
    name="MyReactChatAgent",
    instructions="You are a helpful assistant for a website chat interface."
)

# AG UI Protocol: SSE Streaming endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Server-Sent Events endpoint following AG UI Protocol.
    Streams agent responses using proper AG UI events.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        thread_id = request.thread_id or str(uuid.uuid4())
        run_id = request.run_id or str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        try:
            # RUN_STARTED event
            run_started = RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=thread_id,
                run_id=run_id,
                timestamp=int(datetime.now(UTC).timestamp() * 1000)
            )
            yield f"data: {run_started.model_dump_json()}\n\n"
            
            # TEXT_MESSAGE_START event
            msg_start = TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant",
                timestamp=int(datetime.now(UTC).timestamp() * 1000)
            )
            yield f"data: {msg_start.model_dump_json()}\n\n"
            
            # Run agent (if your agent supports streaming, stream chunks here)
            result = await agent.run(request.message)
            
            # TEXT_MESSAGE_CONTENT event (can be sent in chunks)
            msg_content = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=result.text,
                timestamp=int(datetime.now(UTC).timestamp() * 1000)
            )
            yield f"data: {msg_content.model_dump_json()}\n\n"
            
            # TEXT_MESSAGE_END event
            msg_end = TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=message_id,
                timestamp=int(datetime.now(UTC).timestamp() * 1000)
            )
            yield f"data: {msg_end.model_dump_json()}\n\n"
            
            # RUN_FINISHED event
            run_finished = RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=thread_id,
                run_id=run_id,
                timestamp=int(datetime.now(UTC).timestamp() * 1000)
            )
            yield f"data: {run_finished.model_dump_json()}\n\n"
            
        except Exception as e:
            # RUN_ERROR event
            run_error = RunErrorEvent(
                type=EventType.RUN_ERROR,
                message=str(e),
                timestamp=int(datetime.now(UTC).timestamp() * 1000)
            )
            yield f"data: {run_error.model_dump_json()}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: str = Form(...)):
    try:
        result = await agent.run(message)
        return ChatResponse(reply=result.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                run_id = str(uuid.uuid4())
                message_id = str(uuid.uuid4())
                
                if not user_message:
                    error_event = RunErrorEvent(
                        type=EventType.RUN_ERROR,
                        message="No message provided",
                        timestamp=int(datetime.now(UTC).timestamp() * 1000)
                    )
                    await websocket.send_text(error_event.model_dump_json())
                    continue
                
                # RUN_STARTED event
                run_started = RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=thread_id,
                    run_id=run_id,
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(run_started.model_dump_json())
                
                # TEXT_MESSAGE_START event
                msg_start = TextMessageStartEvent(
                    type=EventType.TEXT_MESSAGE_START,
                    message_id=message_id,
                    role="assistant",
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(msg_start.model_dump_json())
                
                # Run agent
                result = await agent.run(user_message)
                
                # TEXT_MESSAGE_CONTENT event
                msg_content = TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=result.text,
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(msg_content.model_dump_json())
                
                # TEXT_MESSAGE_END event
                msg_end = TextMessageEndEvent(
                    type=EventType.TEXT_MESSAGE_END,
                    message_id=message_id,
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(msg_end.model_dump_json())
                
                # RUN_FINISHED event
                run_finished = RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=thread_id,
                    run_id=run_id,
                    timestamp=int(datetime.now(UTC).timestamp() * 1000)
                )
                await websocket.send_text(run_finished.model_dump_json())
                
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

# Form data endpoint (for your frontend form submission)
@app.post("/chat/form", response_model=ChatResponse)
async def chat_form_endpoint(
    message: str = Form(...),
    user_id: str = Form(default="default")
):
    try:
        result = await agent.run(message)
        return ChatResponse(reply=result.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# If you want streaming:
# @app.websocket("/ws/chat")
# … etc.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)