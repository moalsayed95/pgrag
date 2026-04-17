# Function Calling

Normally an LLM only returns text. **Function calling** lets you give the LLM a menu of tools (Python functions) it can choose to invoke.

## How it works

1. You describe your function(s) to OpenAI — name, description, parameters.
2. You send the user's message.
3. OpenAI decides: *"I need to call that function."* It returns the function name + arguments — **it does not run it**.
4. **Your code** runs the function and sends the result back.
5. OpenAI uses the result to write the final answer.

```
User message
    │
    ▼
OpenAI ──► "call play_song({artist, song})"
    │
    ▼
Your code runs play_song()
    │
    ▼
OpenAI ──► final answer to user
```

The LLM never executes code. It just decides *when* and *how* to call — you do the actual work.
