from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from typing import Any, List, Optional


def sanitize_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """Convert messages to MiniMax-compatible format
    
    - Strips image_url from content arrays (MiniMax is text-only)
    - Keeps AIMessage.tool_calls intact (model needs action format examples)
    - Converts role='tool' → HumanMessage (hub1 doesn't support 'tool' role)
    """
    sanitized = []
    for msg in messages:
        # 1. AIMessage with tool_calls → keep original (preserves tool_calls + content)
        if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
            sanitized.append(AIMessage(content=" ", tool_calls=msg.tool_calls))
            continue
        
        # 2. Content array → string (strip images, keep text)
        content = msg.content
        if isinstance(content, list):
            text_parts = [
                part["text"] for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            content = " ".join(text_parts)
        
        # 3. role 'tool' → HumanMessage (hub1 doesn't support 'tool' role)
        if msg.type == "tool":
            sanitized.append(HumanMessage(content=content))
        else:
            sanitized.append(msg.__class__(content=content))
    
    return sanitized


import json


def _dump_messages(messages):
    rows = []
    for i, msg in enumerate(messages):
        row = {"i": i, "role": msg.type}
        if isinstance(msg, ToolMessage):
            row["tool_call_id"] = msg.tool_call_id
        if msg.content:
            row["content"] = str(msg.content)[:200]
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            calls = []
            for tc in msg.tool_calls:
                calls.append({"id": tc.get("id", ""), "name": tc.get("name", tc.get("function", {}).get("name", "")), "args_preview": str(tc.get("args", tc.get("function", {}).get("arguments", "")))[:100]})
            row["tool_calls"] = calls
        rows.append(row)
    return json.dumps(rows, indent=2, ensure_ascii=False)


class SanitizingChatOpenAI(ChatOpenAI):
    """ChatOpenAI wrapper for MiniMax-compatible APIs.
    
    - Sanitizes messages (tool role → HumanMessage, array content → string)
    - Reverts max_completion_tokens → max_tokens (LangChain renames it, but
      MiniMax/hub1 API expects max_tokens, not max_completion_tokens)
    """
    
    def _get_request_payload(self, messages, stop=None, **kwargs):
        payload = super()._get_request_payload(messages, stop=stop, **kwargs)
        if "max_completion_tokens" in payload and "max_tokens" not in payload:
            payload["max_tokens"] = payload.pop("max_completion_tokens")
        return payload
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        print(f"\n========== [DEBUG LLM REQUEST - BEFORE SANITIZE] ==========\n{_dump_messages(messages)}")
        clean = sanitize_messages(messages)
        print(f"\n========== [DEBUG LLM REQUEST - AFTER SANITIZE] ==========\n{_dump_messages(clean)}")
        print(f"\n========== [DEBUG LLM KWARGS - SYNC] ==========\n{kwargs}")
        return super()._generate(clean, stop=stop, run_manager=run_manager, **kwargs)
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        print(f"\n========== [DEBUG LLM REQUEST - BEFORE SANITIZE] ==========\n{_dump_messages(messages)}")
        clean = sanitize_messages(messages)
        print(f"\n========== [DEBUG LLM REQUEST - AFTER SANITIZE] ==========\n{_dump_messages(clean)}")
        print(f"\n========== [DEBUG LLM KWARGS - ASYNC] ==========\n{kwargs}")
        return await super()._agenerate(clean, stop=stop, run_manager=run_manager, **kwargs)


class ProbingChatOpenAI(SanitizingChatOpenAI):
    """Temporary probe that prints the final request payload before dispatch."""

    def _get_request_payload(self, messages, stop=None, **kwargs):
        payload = super()._get_request_payload(messages, stop=stop, **kwargs)
        print("\n========== [DEBUG FINAL REQUEST PAYLOAD] ==========")
        print(payload)
        return payload
