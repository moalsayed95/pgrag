from fastmcp import FastMCP

mcp = FastMCP("HelloMCP")


@mcp.tool
def greet(name: str) -> str:
    """Say hello to someone. The LLM will call this when it needs to greet a user."""
    return f"Hello, {name}! Welcome to MCP."


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run()
