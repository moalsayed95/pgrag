from fastmcp import FastMCP

mcp = FastMCP(
    "HttpDemo",
    instructions="A demo MCP server running over HTTP. Has tools for text analysis.",
)


@mcp.tool
def word_count(text: str) -> dict:
    """Count words, characters, and lines in a text."""
    lines = text.split("\n")
    words = text.split()
    return {
        "lines": len(lines),
        "words": len(words),
        "characters": len(text),
    }


@mcp.tool
def summarize_stats(numbers: list[float]) -> dict:
    """Calculate basic statistics for a list of numbers."""
    if not numbers:
        return {"error": "empty list"}
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "mean": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
    }


if __name__ == "__main__":

    mcp.run(transport="http", host="127.0.0.1", port=8001)
