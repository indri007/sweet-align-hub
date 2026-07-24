"""
Compatibility shim for a packaging bug in ragas 0.3.x.

`ragas.llms.base` does an unconditional top-level import:
    from langchain_community.chat_models.vertexai import ChatVertexAI

That submodule was removed from `langchain-community` (ChatVertexAI moved to
the separate `langchain-google-vertexai` package), so importing `ragas` at
all raises `ModuleNotFoundError`, even if you never use Vertex AI.
See: https://github.com/vibrantlabsai/ragas/issues/2745

This project only uses Google Gemini (via `langchain-google-genai`), never
Vertex AI, so we register a harmless stub module in `sys.modules` under the
old import path. If someone ever actually tries to use it, it raises a clear
error instead of silently pretending to work.

Usage: call `apply_ragas_compat_shim()` before importing anything from `ragas`.
"""

import sys
import types


def apply_ragas_compat_shim() -> None:
    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return

    try:
        # If a real ChatVertexAI is importable (e.g. langchain-google-vertexai
        # is installed), prefer wiring that in instead of a stub.
        from langchain_google_vertexai import ChatVertexAI  # type: ignore
    except ImportError:
        class ChatVertexAI:  # noqa: N801 - matching the real class name
            """Stub: Vertex AI is not used in this project."""

            def __init__(self, *args, **kwargs):
                raise RuntimeError(
                    "ChatVertexAI is a compatibility stub — this project uses "
                    "Google Gemini via langchain-google-genai, not Vertex AI. "
                    "Install `langchain-google-vertexai` if you actually need it."
                )

    stub = types.ModuleType(module_name)
    stub.ChatVertexAI = ChatVertexAI
    sys.modules[module_name] = stub
