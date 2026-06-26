# 🤖 AgentDesk — A Tool-Calling AI Agent

AgentDesk is a minimal but complete implementation of the agentic pattern that powers modern AI products: an LLM that can decide, on its own, when to call external tools (web search, a calculator, a file reader), execute them, and weave the results into a final answer.

## Why this project

"Agentic AI" is the most current and in-demand pattern in AI engineering right now (function calling, tool use, multi-step reasoning loops). This project strips it down to its essentials so you can clearly explain — in an interview — exactly how it works, with no framework magic hiding the logic.

## How it works

1. User sends a message.
2. The message + tool schemas are sent to Claude.
3. If Claude decides it needs a tool, it returns a `tool_use` block instead of a final answer.
4. AgentDesk executes the requested tool(s) locally and sends the results back to Claude.
5. Claude either calls another tool or returns a final, grounded answer.
6. This loop repeats (capped at `MAX_TURNS`) until a final answer is produced.

## Tools included

| Tool | What it does | Safety notes |
|---|---|---|
| `calculator` | Evaluates arithmetic expressions | Uses AST parsing, not `eval()` — cannot execute arbitrary code |
| `web_search` | Searches DuckDuckGo for current info | No API key required |
| `read_file` | Reads text files | Sandboxed to a local `./files` directory only — cannot read arbitrary paths |

## Setup

```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# edit .env and add your ANTHROPIC_API_KEY

# Windows PowerShell:
$env:ANTHROPIC_API_KEY = "your-key-here"
python agent.py
```

## Example session

```
You: What's 18% tip on a $64.50 bill, and is that a typical tip rate in Canada?
  🔧 Calling tool: calculator({'expression': '64.50 * 0.18'})
  🔧 Calling tool: web_search({'query': 'typical tip rate Canada restaurants'})

AgentDesk: An 18% tip on $64.50 is $11.61. Based on current sources, 15-20%
is the typical tipping range in Canada, so 18% is right in the normal range.
```

## Future improvements

- Add a "code execution" tool (sandboxed) for data analysis questions
- Add conversation memory across sessions
- Wrap in a simple Streamlit chat UI instead of CLI
