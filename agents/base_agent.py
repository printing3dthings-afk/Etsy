import anthropic
from typing import Any
from config import MODEL, MAX_TOKENS, MAX_ITERATIONS


class BaseAgent:
    """Base class for all Etsy hub agents."""

    def __init__(self, name: str, system_prompt: str, tool_definitions: list[dict]):
        self.name = name
        self.system_prompt = system_prompt
        self.tool_definitions = tool_definitions
        self.client = anthropic.Anthropic()

    def run(self, task: str, max_iterations: int = MAX_ITERATIONS) -> str:
        """Run the agent on a task, handling the full tool-use loop."""
        messages: list[dict] = [{"role": "user", "content": task}]

        for iteration in range(max_iterations):
            response = self._call_api(messages)

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                tool_results = self._process_tool_calls(response)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            return self._extract_text(response) or f"[{self.name}] Stopped: {response.stop_reason}"

        return f"[{self.name}] Reached max iterations ({max_iterations}) without completing."

    def _call_api(self, messages: list[dict]) -> anthropic.types.Message:
        kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": [
                {
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": messages,
        }
        if self.tool_definitions:
            kwargs["tools"] = self.tool_definitions
        return self.client.messages.create(**kwargs)

    def _extract_text(self, response: anthropic.types.Message) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()

    def _process_tool_calls(self, response: anthropic.types.Message) -> list[dict]:
        results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    output = self.execute_tool(block.name, block.input)
                except Exception as exc:
                    output = f"Tool error: {exc}"
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(output),
                    }
                )
        return results

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Override in subclasses to handle tool calls."""
        return f"Unknown tool: {tool_name}"
