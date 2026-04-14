import asyncio
from fastmcp import Client


async def main():
    async with Client("http://127.0.0.1:8001/mcp") as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        print()

        result = await client.call_tool("word_count", {"text": "Hello world\nThis is MCP"})
        print(f"word_count result: {result}")

        result = await client.call_tool("summarize_stats", {"numbers": [1, 2, 3, 4, 5]})
        print(f"summarize_stats result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
