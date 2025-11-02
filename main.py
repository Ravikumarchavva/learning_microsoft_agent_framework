from agent_framework import ChatAgent, ai_function
from agent_framework.openai import OpenAIChatClient

# Create simple tools for the example
@ai_function
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: sunny"

@ai_function
def get_time() -> str:
    """Get current time."""
    return "Current time: 2:30 PM"

# Create client
client = OpenAIChatClient(model_id="gpt-5")

async def example():
    # Direct creation
    agent = ChatAgent(
        name="assistant",
        chat_client=client,
        instructions="You are a helpful assistant.",
        tools=[get_weather]  # Multi-turn by default
    )

    # Factory method (more convenient)
    agent = client.create_agent(
        name="assistant",
        instructions="You are a helpful assistant.",
        tools=[get_weather]
    )

    # Execution with runtime tool configuration
    result = await agent.run(
        "What's the weather in Bangkok?",
        tools=[get_time],  # Can add tools at runtime
        tool_choice="auto"
    )
    print(result)

# Assume we have client, agent, and tools from previous examples
async def streaming_example():

    agent = ChatAgent(
        name="assistant",
        chat_client=client,
        instructions="You are a helpful assistant.",
        tools=[get_weather]  # Multi-turn by default
    )

    # Agent streaming
    async for chunk in agent.run_stream("Hello can you tell me about india history?"):
        if chunk.text:
            print(chunk.text, end="", flush=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(streaming_example())