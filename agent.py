"""
agent.py
--------
The agentic loop: send the user's message to Claude with tool
definitions attached, execute whichever tool(s) Claude asks for,
feed the results back, and repeat until Claude gives a final answer.
This is the core pattern behind every "AI agent" product you've seen -
there's no separate "agent brain", it's just this loop.

DEMO_MODE: if no ANTHROPIC_API_KEY is set, AgentDesk falls back to
canned example responses so the project can still be demoed live
without requiring a paid API key. Real usage (with a key) always
uses the genuine Anthropic agent loop below.
"""
import os
import anthropic
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

MODEL = "claude-sonnet-4-6"
MAX_TURNS = 6  # safety cap so a buggy tool loop can't run forever

DEMO_RESPONSES = {
    "default": (
        "[DEMO MODE] AgentDesk would normally call Claude with tool access "
        "(calculator, web search, file reader) to answer this. Add a real "
        "ANTHROPIC_API_KEY environment variable to see live responses.\n\n"
        "Example: ask 'What is 1432 * 87?' to see a simulated calculator tool call below."
    ),
    "calculator_example": (
        "🔧 Calling tool: calculator({'expression': '1432 * 87'})\n"
        "Tool result: 124584\n\n"
        "AgentDesk: 1432 * 87 = 124584. I used the calculator tool to compute this precisely."
    ),
}

class AgentDesk:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.demo_mode = api_key is None
        self.system_prompt = (
            "You are AgentDesk, a helpful assistant with access to tools: "
            "a calculator, a web search, and a sandboxed file reader. "
            "Use tools whenever they would give you better/more current "
            "information than your own knowledge. Always explain your "
            "final answer clearly, and mention which tool(s) you used."
        )
        if self.demo_mode:
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

    def run(self, user_message: str, verbose: bool = True) -> str:
        if self.demo_mode:
            if "*" in user_message or "multiply" in user_message.lower():
                return DEMO_RESPONSES["calculator_example"]
            return DEMO_RESPONSES["default"]

        messages = [{"role": "user", "content": user_message}]
        for turn in range(MAX_TURNS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1000,
                system=self.system_prompt,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "tool_use":
                final_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                return final_text
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_name = block.name
                tool_input = block.input
                if verbose:
                    print(f"  🔧 Calling tool: {tool_name}({tool_input})")
                func = TOOL_FUNCTIONS.get(tool_name)
                if func is None:
                    result = f"Unknown tool: {tool_name}"
                else:
                    result = func(**tool_input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )
            messages.append({"role": "user", "content": tool_results})
        return "Reached maximum tool-use turns without a final answer."


if __name__ == "__main__":
    agent = AgentDesk()
    if agent.demo_mode:
        print("AgentDesk ready (DEMO MODE - no API key detected). Type 'exit' to quit.\n")
    else:
        print("AgentDesk ready. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        answer = agent.run(user_input)
        print(f"\nAgentDesk: {answer}\n")