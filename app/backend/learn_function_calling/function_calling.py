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
        },
    }
]

# ── 3. First call: let OpenAI decide whether to use the tool ─────────────────

user_message = "Play Thriller by Michael Jackson"
print(f"User: {user_message}\n")

# Keep a running input list — we'll append to it across both API calls
input_list = [{"role": "user", "content": user_message}]

response = client.responses.create(
    model="gpt-4o-mini",
    tools=TOOLS,
    input=input_list,
)

# Append OpenAI's full output turn to the conversation history
input_list += response.output

# ── 4. Check if OpenAI wants to call a function ───────────────────────────────

for item in response.output:
    if item.type == "function_call":
        args = json.loads(item.arguments)
        print(f"OpenAI wants to call: {item.name}({args})")

        # ── 5. Your code runs the function ────────────────────────────────────
        result = play_song(**args)
        print(f"Function returned: {result}\n")

        # ── 6. Append the result so OpenAI can see it ─────────────────────────
        input_list.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": result,
        })

# ── 7. Second call: OpenAI writes the final answer using the tool result ──────
final = client.responses.create(
    model="gpt-4o-mini",
    instructions="Confirm the song is now playing based on the tool result.",
    tools=TOOLS,
    input=input_list,
)
print(f"Assistant: {final.output_text}")
