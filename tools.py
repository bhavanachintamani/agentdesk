"""
tools.py
--------
Tool implementations for AgentDesk. Each tool is a plain Python function
plus a JSON schema describing it (used for Anthropic tool-calling).
Keeping tools as simple, testable functions is intentional - it shows
you understand that "agents" are really just LLMs + a dispatch loop
over deterministic functions, not magic.
"""

import ast
import operator
import os

import requests

# ---------------------------------------------------------------------
# Tool 1: Calculator (safe — uses AST evaluation, not eval())
# ---------------------------------------------------------------------
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Evaluates a basic arithmetic expression safely (no eval())."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


# ---------------------------------------------------------------------
# Tool 2: Web search (DuckDuckGo HTML — no API key required)
# ---------------------------------------------------------------------
def web_search(query: str, max_results: int = 3) -> str:
    """Searches the web via DuckDuckGo's HTML endpoint and returns
    a few result snippets. No API key required, which keeps this
    project runnable by anyone who clones the repo."""
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        resp.raise_for_status()
    except Exception as e:
        return f"Search failed: {e}"

    # Lightweight parsing without an extra dependency like BeautifulSoup
    import re

    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text)

    cleaned = []
    for t, s in zip(titles[:max_results], snippets[:max_results]):
        clean_title = re.sub("<.*?>", "", t)
        clean_snippet = re.sub("<.*?>", "", s)
        cleaned.append(f"- {clean_title}: {clean_snippet}")

    return "\n".join(cleaned) if cleaned else "No results found."


# ---------------------------------------------------------------------
# Tool 3: File reader (sandboxed to a local ./files directory)
# ---------------------------------------------------------------------
SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "files")
os.makedirs(SANDBOX_DIR, exist_ok=True)


def read_file(filename: str) -> str:
    """Reads a text file from the sandboxed ./files directory only -
    deliberately cannot read arbitrary paths on disk."""
    safe_name = os.path.basename(filename)  # strip any path traversal attempt
    path = os.path.join(SANDBOX_DIR, safe_name)
    if not os.path.exists(path):
        return f"File '{safe_name}' not found in sandbox directory ({SANDBOX_DIR})."
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:3000]  # cap to keep prompts small
    except Exception as e:
        return f"Error reading file: {e}"


# ---------------------------------------------------------------------
# Tool registry + JSON schemas for the LLM
# ---------------------------------------------------------------------
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "web_search": web_search,
    "read_file": read_file,
}

TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '12 * (4 + 3)'.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for current information and return top result snippets.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a text file located in the agent's local ./files sandbox directory.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
]
