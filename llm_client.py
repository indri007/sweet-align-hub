"""
Unified LLM client wrapper.

Lets the rest of the app call one function, `chat_completion()`, regardless
of whether the configured provider is Google Gemini or OpenAI. Provider is
selected via config.LLM_PROVIDER (auto-detected from whichever API key is
present in .env, or set explicitly with LLM_PROVIDER=gemini|openai).

Usage:
    from llm_client import chat_completion

    text = chat_completion(
        messages=[
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
        ],
        temperature=0.7,
        max_tokens=1000,
    )
"""

import config


def is_llm_configured() -> bool:
    return config.is_llm_configured()


def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 1500) -> str:
    """
    Send a chat-style request to whichever LLM provider is configured.

    `messages` follows the OpenAI format:
        [{"role": "system"/"user"/"assistant", "content": "..."}]

    Returns the assistant's reply text as a string.
    Raises an Exception on failure -- callers should catch and handle.
    """
    if config.LLM_PROVIDER == "gemini":
        return _gemini_chat(messages, temperature, max_tokens)
    elif config.LLM_PROVIDER == "openai":
        return _openai_chat(messages, temperature, max_tokens)
    else:
        raise RuntimeError(
            "Tidak ada LLM yang dikonfigurasi. Set GEMINI_API_KEY atau OPENAI_API_KEY di .env"
        )


def _openai_chat(messages: list[dict], temperature: float, max_tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _gemini_chat(messages: list[dict], temperature: float, max_tokens: int) -> str:
    from google import genai
    from google.genai import types

    client = config.get_gemini_client()

    # Gemini keeps system instructions separate from the conversation turns,
    # and uses role "model" instead of "assistant".
    system_parts = []
    contents = []
    for msg in messages:
        role = msg.get("role")
        text = msg.get("content", "") or ""
        if role == "system":
            system_parts.append(text)
        elif role == "user":
            contents.append(types.Content(role="user", parts=[types.Part(text=text)]))
        elif role == "assistant":
            contents.append(types.Content(role="model", parts=[types.Part(text=text)]))

    system_instruction = "\n\n".join(system_parts) if system_parts else None

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text
