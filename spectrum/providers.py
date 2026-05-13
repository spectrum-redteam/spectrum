"""
spectrum/providers.py
=====================
Unified interface for HuggingFace, Gemini, and AMD backends.
All LLM calls in Spectrum go through here.
"""
import os
import re
import time
import json
import requests as req
from rich.console import Console
from huggingface_hub import InferenceClient

console = Console()

# Gemini is optional – only imported when actually needed
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# ----------------------------------------------------------------------
# Helper: load config from the standard path
# ----------------------------------------------------------------------
def _get_config_path():
    """Return the absolute path to config.json."""
    return os.path.join(os.path.dirname(__file__), "config.json")

def _load_config():
    with open(_get_config_path(), "r") as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Gemini setup
# ----------------------------------------------------------------------
def _init_gemini(config):
    if genai is None:
        raise RuntimeError(
            "google-genai is not installed. "
            "Run: pip install google-genai"
        )
    api_key = config.get("api_key") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Gemini provider selected but no api_key set. "
            "Use Settings to add your key."
        )
    client = genai.Client(api_key=api_key)
    return client

# ----------------------------------------------------------------------
# Core call – all providers
# ----------------------------------------------------------------------
def generate(
    messages,
    config=None,
    *,
    model_id=None,
    temperature=None,
    max_tokens=None,
    retries=3,
):
    """
    Send a chat conversation and return the assistant's text.

    Parameters
    ----------
    messages : list of dict
        Each dict with 'role' ('system', 'user', 'assistant') and 'content'.
    config : dict or None
        Loaded config.json dictionary. If None, loads automatically.
    model_id : str or None
        Override the final model ID. For Gemini this is ignored.
    temperature, max_tokens : override config values.
    retries : int
        Number of attempts on transient errors.

    Returns
    -------
    str – the assistant response, or an error string starting with "Error:".
    """
    if config is None:
        config = _load_config()

    provider = config.get("provider", "huggingface").lower()
    temp = temperature if temperature is not None else config.get("temperature", 0.4)
    mtokens = max_tokens if max_tokens is not None else config.get("max_tokens_per_request", 8000)

    # ---------- Gemini ----------
    if provider == "gemini":
        client = _init_gemini(config)
        model_name = config.get("gemini_model", "gemini-2.5-flash")

        # Build prompt from messages
        system_parts = []
        conversation = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_parts.append(content)
            elif role == "user":
                text = content
                if system_parts:
                    text = "[System]\n" + "\n".join(system_parts) + "\n\n" + text
                    system_parts.clear()
                conversation.append(types.Content(
                    role="user",
                    parts=[types.Part(text=text)]
                ))
            elif role == "assistant":
                conversation.append(types.Content(
                    role="model",
                    parts=[types.Part(text=content)]
                ))

        # Handle any remaining system messages
        if system_parts:
            if conversation and conversation[-1].role == "user":
                existing = conversation[-1].parts[0].text
                conversation[-1] = types.Content(
                    role="user",
                    parts=[types.Part(text="[System]\n" + "\n".join(system_parts) + "\n\n" + existing)]
                )
            else:
                conversation.append(types.Content(
                    role="user",
                    parts=[types.Part(text="[System]\n" + "\n".join(system_parts))]
                ))

        for attempt in range(retries):
            try:
                with console.status("[bold cyan]Agent Cognition (Gemini)...", spinner="line"):
                    response = client.models.generate_content(
                        model=model_name,
                        contents=conversation,
                        config=types.GenerateContentConfig(
                            temperature=temp,
                            max_output_tokens=mtokens,
                        ),
                    )
                return response.text
            except Exception as e:
                err_str = str(e).lower()
                if "quota" in err_str or "429" in err_str:
                    console.print("[bold red]Gemini quota exhausted.[/bold red]")
                elif "api_key" in err_str or "invalid" in err_str:
                    return "Error: Invalid Gemini API Key"
                console.print(f"[yellow]Gemini attempt {attempt+1} failed: {e}[/yellow]")
                time.sleep(5 * (2 ** attempt))
        return "Error: Gemini API Timeout"

    # ---------- HuggingFace ----------
    if provider == "huggingface":
        token = os.environ.get("HF_TOKEN")
        hf_model = model_id or config.get("final_model_id")
        for attempt in range(retries):
            try:
                client = InferenceClient(model=hf_model, token=token)
                with console.status("[bold cyan]Agent Cognition (HF)...", spinner="line"):
                    response = client.chat_completion(
                        messages=messages,
                        max_tokens=mtokens,
                        temperature=temp,
                    )
                msg = response.choices[0].message
                reasoning = getattr(msg, "reasoning", None)
                if reasoning:
                    return f"\u4DC2\n{reasoning}\n\u4DC2\n" + (msg.content or "")
                return msg.content or ""
            except Exception as e:
                err_str = str(e).lower()
                if "402" in err_str or "payment required" in err_str:
                    return "Error: 402"
                time.sleep(5 * (2 ** attempt))
        return "Error: HF API Timeout"

    # ---------- AMD ----------
    if provider == "amd":
        api_key = os.environ.get("AMD_API_KEY")
        endpoint = config.get("amd_config", {}).get("endpoint", "https://api.amd.com/v1")
        amd_model = model_id or config.get("final_model_id")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": amd_model,
            "messages": messages,
            "max_tokens": mtokens,
            "temperature": temp,
        }
        for attempt in range(retries):
            try:
                with console.status("[bold cyan]Agent Cognition (AMD)...", spinner="line"):
                    resp = req.post(
                        f"{endpoint}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=120,
                    )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 402:
                    return "Error: 402"
                else:
                    console.print(f"[yellow]AMD error {resp.status_code}: {resp.text[:200]}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]AMD request failed: {e}[/yellow]")
            time.sleep(5 * (2 ** attempt))
        return "Error: AMD API Timeout"

    return f"Error: Unknown provider '{provider}'"