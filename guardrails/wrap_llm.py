"""Wrap each agent LLM call with RunnableRails (input → Groq → output)."""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails

from guardrails.rails_config import load_rails_config

_REFUSAL_MARKERS = (
    "i'm sorry, i can't respond to that",
    "i can't respond to that",
    "i cannot respond to that",
)


@lru_cache(maxsize=1)
def _runnable_rails() -> RunnableRails:
    return RunnableRails(config=load_rails_config(), passthrough=True)


def looks_like_guardrail_refusal(text: str | None) -> bool:
    if not text:
        return True
    lowered = text.strip().lower()
    return any(marker in lowered for marker in _REFUSAL_MARKERS)


def invoke_guarded_chat(
    model: str,
    *,
    system: str,
    user: str,
    response_format: dict | None = None,
    max_tokens: int = 2000,
    reasoning_effort: str | None = "low",
) -> str:
    """Call Groq through RunnableRails and return the text content."""
    llm = ChatOpenAI(
        model=model,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        max_tokens=max_tokens,
    )
    bind_kwargs: dict = {}
    if response_format is not None:
        bind_kwargs["response_format"] = response_format
    if reasoning_effort is not None:
        bind_kwargs["reasoning_effort"] = reasoning_effort
    if bind_kwargs:
        llm = llm.bind(**bind_kwargs)

    guarded = _runnable_rails() | llm
    messages: list[BaseMessage] = [
        SystemMessage(content=system),
        HumanMessage(content=user),
    ]
    result = guarded.invoke(messages)

    if isinstance(result, AIMessage):
        return str(result.content or "")
    if isinstance(result, dict):
        for key in ("output", "content", "answer"):
            if key in result and result[key] is not None:
                return str(result[key])
        return str(result)
    return str(result)
