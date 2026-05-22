from __future__ import annotations

import anthropic
import concurrent.futures
import hashlib
import json
import logging
import os
import threading
import time
from logging.handlers import RotatingFileHandler
from typing import Any
from config import MAX_TOKENS, MAX_ITERATIONS
from tools import web_research_tools, learning_tools

# Keep last N assistant/user pairs before trimming; guards against context bloat on long runs.
_MAX_HISTORY_PAIRS = 6
# Circuit-break if the same tool is called with identical inputs this many times in one run.
_MAX_TOOL_REPEATS = 3


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
        # Merge domain tools with universal research + learning tools; deduplicate by name
        merged = tool_definitions + self._UNIVERSAL_TOOLS
        seen: set[str] = set()
        deduped: list[dict] = []
        for t in merged:
            n = t.get("name")
            if n not in seen:
                seen.add(n)
                deduped.append(t)
        self.tool_definitions = deduped
        from config import STANDARD_MODEL
        self.model = model or STANDARD_MODEL
        self.client = anthropic.Anthropic()
        self.logger = _get_logger(name)

    def run(self, task: str, max_iterations: int = MAX_ITERATIONS) -> str:
        """Run the agent on a task, handling the full tool-use loop."""
        self.logger.info(f"START task={task[:80]}")
        messages: list[dict] = [{"role": "user", "content": task}]

        # Track (tool_name::input_hash) → call count for stuck-loop detection.
        _tool_call_counts: dict[str, int] = {}
        _in_tokens = 0
        _out_tokens = 0

        for _ in range(max_iterations):
            messages = self._trim_history(messages)
            response = self._call_api(messages)

            # Accumulate token usage for monitoring.
            if hasattr(response, "usage"):
                _in_tokens += getattr(response.usage, "input_tokens", 0)
                _out_tokens += getattr(response.usage, "output_tokens", 0)

            if response.stop_reason == "end_turn":
                self.logger.info(
                    f"END stop_reason=end_turn tokens=in:{_in_tokens}/out:{_out_tokens}"
                )
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                # Check for stuck loops before dispatching.
                loop_tools: list[str] = []
                for block in response.content:
                    if block.type == "tool_use":
                        try:
                            input_hash = hashlib.md5(
                                json.dumps(block.input, sort_keys=True).encode()
                            ).hexdigest()[:8]
                        except (TypeError, ValueError):
                            input_hash = "unhashable"
                        key = f"{block.name}::{input_hash}"
                        _tool_call_counts[key] = _tool_call_counts.get(key, 0) + 1
                        if _tool_call_counts[key] >= _MAX_TOOL_REPEATS:
                            loop_tools.append(block.name)

                if loop_tools:
                    self.logger.warning(
                        f"Stuck-loop detected: {loop_tools} called {_MAX_TOOL_REPEATS}x "
                        "with identical inputs. Injecting break."
                    )

                tool_results = self._process_tool_calls(response)
                messages.append({"role": "assistant", "content": response.content})

                if loop_tools:
                    # Append tool results alongside a break nudge so the agent must synthesize.
                    messages.append({
                        "role": "user",
                        "content": tool_results + [{
                            "type": "text",
                            "text": (
                                f"WARNING: You have called {loop_tools} with the same inputs "
                                f"{_MAX_TOOL_REPEATS} times and are in a loop. "
                                "Do NOT call any more tools. Synthesize a final answer from "
                                "the information you already have and stop."
                            ),
                        }],
                    })
                else:
                    messages.append({"role": "user", "content": tool_results})
                continue

            self.logger.info(f"END stop_reason={response.stop_reason}")
            return self._extract_text(response) or f"[{self.name}] Stopped: {response.stop_reason}"

        self.logger.warning(
            f"Reached max iterations ({max_iterations}) "
            f"tokens=in:{_in_tokens}/out:{_out_tokens}"
        )
        return f"[{self.name}] Reached max iterations ({max_iterations}) without completing."

    def _trim_history(self, messages: list[dict]) -> list[dict]:
        """Keep the initial user message + the most recent N assistant/user pairs."""
        if len(messages) <= 1 + _MAX_HISTORY_PAIRS * 2:
            return messages
        recent = messages[1:]
        keep = recent[-(_MAX_HISTORY_PAIRS * 2):]
        trimmed_count = len(recent) - len(keep)
        if trimmed_count:
            self.logger.debug(f"Trimmed {trimmed_count} old messages to stay within context")
        return [messages[0]] + keep

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

        delays = [5, 15, 30]
        last_exc: Exception | None = None
        for attempt in range(4):
            if attempt > 0:
                wait = delays[attempt - 1]
                self.logger.warning(f"Anthropic rate limit — retrying in {wait}s (attempt {attempt+1}/4)")
                time.sleep(wait)
            try:
                return self.client.messages.create(**kwargs)
            except anthropic.RateLimitError as e:
                last_exc = e
            except anthropic.APIStatusError as e:
                if e.status_code in (529, 503, 500):
                    last_exc = e
                else:
                    raise
            except anthropic.APIConnectionError as e:
                last_exc = e

        self.logger.error(f"Anthropic API failed after 4 attempts: {last_exc}")
        raise RuntimeError(f"Anthropic API unavailable after retries: {last_exc}") from last_exc

    def _extract_text(self, response: anthropic.types.Message) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()

    def _process_tool_calls(self, response: anthropic.types.Message) -> list[dict]:
        """Dispatch tool calls — parallel when multiple independent calls are returned."""
        tool_blocks = [b for b in response.content if b.type == "tool_use"]

        if len(tool_blocks) <= 1:
            # Single tool — simple sequential path, no threading overhead.
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        output = self._dispatch_tool(block.name, block.input)
                    except Exception as exc:
                        self.logger.error(f"Tool {block.name} failed: {exc}", exc_info=True)
                        output = f"Tool error: {exc}"
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(output),
                    })
            return results

        # Multiple tool calls — fan out in parallel threads to minimize latency.
        ordered: list[dict | None] = [None] * len(tool_blocks)
        lock = threading.Lock()

        def _run_one(idx: int, block) -> None:
            try:
                output = self._dispatch_tool(block.name, block.input)
            except Exception as exc:
                self.logger.error(f"Tool {block.name} failed: {exc}", exc_info=True)
                output = f"Tool error: {exc}"
            with lock:
                ordered[idx] = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(output),
                }

        max_workers = min(len(tool_blocks), 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_one, i, b) for i, b in enumerate(tool_blocks)]
            concurrent.futures.wait(futures)

        return [r for r in ordered if r is not None]

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
