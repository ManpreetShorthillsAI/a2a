import os
from typing import List
import google.generativeai as genai
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None


def get_gemini_model(model_name: str = "gemini-1.5-flash", system_instruction: str = ""):
    if load_dotenv:
        try:
            load_dotenv()
        except Exception:
            pass
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    if system_instruction:
        return genai.GenerativeModel(model_name, system_instruction=system_instruction)
    return genai.GenerativeModel(model_name)


def generate_text(prompt: str, system_instruction: str = "") -> str:
    model = get_gemini_model(system_instruction=system_instruction)
    try:
        if model is None:
            raise RuntimeError("GEMINI_API_KEY not configured; using mock response")
        # Use single prompt; system_instruction is already bound to the model
        response = model.generate_content(prompt)
        return (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        return (
            "[MOCKED GEMINI RESPONSE]\n"
            "This is a POC fallback response due to missing key or API error.\n"
            f"Prompt digest: {prompt[:120]}...\n"
            f"Note: {exc}"
        )
