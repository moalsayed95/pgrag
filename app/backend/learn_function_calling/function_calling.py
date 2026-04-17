import json
from openai import OpenAI

client = OpenAI()

# ── 1. The actual function your code runs ─────────────────────────────────────

def play_song(artist: str, song: str) -> str:
    return f"🎵 Now playing: {song} by {artist}"


# ── 2. Describe the function to OpenAI ───────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "name": "play_song",
        "description": "Play a song by a given artist.",
        "parameters": {
            "type": "object",
            "properties": {
                "artist": {"type": "string", "description": "The artist's name."},
                "song":   {"type": "string", "description": "The song title."},
            },
            "required": ["artist", "song"],
            "additionalProperties": False,
        },
    }
]

# ── 3. First call: let OpenAI decide whether to use the tool ─────────────────

user_message = "Play Thriller by Michael Jackson"
print(f"User: {user_message}\n")

response = client.responses.create(
    model="gpt-4o-mini",
    tools=TOOLS,
    input=user_message,
)

# ── 4. Check if OpenAI wants to call a function ───────────────────────────────

tool_call = next(
    (item for item in response.output if item.type == "function_call"),
    None,
)

if tool_call:
    args = json.loads(tool_call.arguments)
    print(f"OpenAI wants to call: {tool_call.name}({args})")

    # ── 5. Your code runs the function ────────────────────────────────────────
    result = play_song(**args)
    print(f"Function returned: {result}\n")

    # ── 6. Send result back — OpenAI writes the final answer ──────────────────
    final = client.responses.create(
        model="gpt-4o-mini",
        tools=TOOLS,
        input=[
            {"role": "user", "content": user_message},
            tool_call,                                   # OpenAI's tool-call turn
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": result,
            },
        ],
    )
    print(f"Assistant: {final.output_text}")
else:
    # OpenAI answered directly without needing the tool
    print(f"Assistant: {response.output_text}")
