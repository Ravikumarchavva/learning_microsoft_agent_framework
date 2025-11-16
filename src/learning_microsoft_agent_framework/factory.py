from agent_framework.openai import OpenAIChatClient
from agent_framework import ChatAgent
from learning_microsoft_agent_framework.configs import Settings

from ag_ui.core import (
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
)
import os
from datetime import datetime, UTC

class Agent:

    def __init__(self, name: str, model: str, instructions: str, tools: list = []):
        self.settings = Settings()
        chat_client = OpenAIChatClient(
            api_key=self.settings.openai_api_key,
            model_id=model
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            instructions=instructions,
            name=name,
            tools=tools
        )

    async def run(self, message: str, user_id: str, thread_id: str, run_id: str, parent_run_id: str = None):
        """
        AG UI Protocol compliant streaming of agent response.
        Yields AG UI events as JSON strings.
        """
        # Run started event (include user_id/thread_id/run_id in raw_event)
        yield RunStartedEvent(
            timestamp=int(datetime.now(UTC).timestamp() * 1000),
            thread_id=thread_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
        )
        try:
            reply_chunks = self.agent.run_stream(messages=message)

            # Text message start event
            message_id = os.urandom(8).hex()
            yield TextMessageStartEvent(
                message_id=message_id,
            )

            # Stream content events (use `delta` per AG UI types)
            async for chunk in reply_chunks:
                # ensure we send only non-empty deltas
                if chunk is None:
                    continue
                chunk_str = str(chunk)
                if not chunk_str:
                    continue

                yield TextMessageContentEvent(
                    message_id=message_id,
                    delta=chunk_str,
                )

            # Text message end event
            yield TextMessageEndEvent(
                message_id=message_id,
            )

            # Run finished event
            yield RunFinishedEvent(
                thread_id=thread_id,
                run_id=run_id,
            )

        except Exception as e:
            # Run error event (AG UI RunErrorEvent uses `message`)
            yield RunErrorEvent(
                message=str(e),
            )
            raise e


if __name__ == "__main__":
    import asyncio

    agent = Agent(
        name="Test Agent",
        model="gpt-4o",
        instructions="You are a helpful assistant."
    )

    async def test():
        async for event_json in agent.run(
            message="Tell me a joke.",
            user_id="user123",
            thread_id="thread123",
            run_id="run123",
            parent_run_id="parent_run123"
        ):
            if hasattr(event_json, "delta"):
                print(event_json.delta, end="", flush=True)

    asyncio.run(test())
