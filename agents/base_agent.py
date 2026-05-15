import anthropic
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from typing import Any
from config import MAX_TOKENS, MAX_ITERATIONS
from tools import web_research_tools, learning_tools


def _get_logger(name: str) -> logging.Logger:
    """Create a configured logger that writes to logs/agents.log and stderr."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured — return as-is to avoid duplicate handlers
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "agents.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


class BaseAgent:
    """Base class for all Etsy hub agents.

    Every agent automatically receives web research tools (research_etsy_market,
    fetch_url, research_product_names, research_design_trends, find_best_keywords)
    and learning tools (save/get_market_insight, save/get strategies, keyword
    performance tracking, design discoveries) via this base class. Subclasses
    add their own domain-specific tools on top.
    """

    _UNIVERSAL_TOOLS = web_research_tools.TOOL_DEFINITIONS + learning_tools.TOOL_DEFINITIONS

    def __init__(self, name: str, system_prompt: str, tool_definitions: list[dict], model: str = ""):
        self.name = name
        self.system_prompt = system_prompt
        # Merge domain tools with universal research + learning tools
        self.tool_definitions = tool_definitions + self._UNIVERSAL_TOOLS
        from config import STANDARD_MODEL
        self.model = model or STANDARD_MODEL
        self.client = anthropic.Anthropic()
        self.logger = _get_logger(name)

    def run(self, task: str, max_iterations: int = MAX_ITERATIONS) -> str:
        """Run the agent on a task, handling the full tool-use loop."""
        self.logger.info(f"START task={task[:80]}")
        messages: list[dict] = [{"role": "user", "content": task}]

        for _ in range(max_iterations):
            response = self._call_api(messages)

            if response.stop_reason == "end_turn":
                self.logger.info(f"END stop_reason={response.stop_reason}")
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                tool_results = self._process_tool_calls(response)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            self.logger.info(f"END stop_reason={response.stop_reason}")
            return self._extract_text(response) or f"[{self.name}] Stopped: {response.stop_reason}"

        return f"[{self.name}] Reached max iterations ({MAX_ITERATIONS}) without completing."

    def _call_api(self, messages: list[dict]) -> anthropic.types.Message:
        kwargs: dict[str, Any] = {
            "model": self.model,
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
                    output = self._dispatch_tool(block.name, block.input)
                except Exception as exc:
                    self.logger.error(f"Tool {block.name} failed: {exc}", exc_info=True)
                    output = f"Tool error: {exc}"
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(output),
                    }
                )
        return results

    def _dispatch_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Route universal tools here; delegate domain tools to subclass."""
        self.logger.info(f"TOOL {tool_name} {list(tool_input.keys())}")
        if tool_name in web_research_tools.TOOL_NAMES:
            output = web_research_tools.execute_tool(tool_name, tool_input)
        elif tool_name in learning_tools.TOOL_NAMES:
            output = learning_tools.execute_tool(tool_name, tool_input, self.name)
        else:
            output = self.execute_tool(tool_name, tool_input)
        self.logger.debug(f"TOOL_RESULT {tool_name}: {str(output)[:200]}")
        return output

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Override in subclasses to handle domain-specific tool calls."""
        return f"Unknown tool: {tool_name}"
