import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

# Automatically load .env file if available
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
MODEL_CANDIDATES = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

def get_groq_model() -> str:
    """Get configured Groq model name from environment or default."""
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

def get_groq_client() -> Groq:
    """
    Get initialized Groq client instance.
    Raises ValueError if GROQ_API_KEY environment variable is not configured.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not configured in backend environment variables. "
            "Please set GROQ_API_KEY in your environment or .env file."
        )
    return Groq(api_key=api_key)

def generate_grounded_answer(
    question: str,
    context_text: str,
    language: str = "English",
    chat_history: list = None,
    is_conversational: bool = False
) -> str:
    """
    Generate an evidence-grounded answer using Groq LLM strictly based on retrieved BIS context.
    Supports English, Hindi (हिंदी), and Marathi (मराठी) output languages.

    Enforces strict grounding rules:
    - Uses ONLY the supplied context text
    - Never uses external memory or outside knowledge
    - Explicitly falls back if context is insufficient
    """
    if not is_conversational and (not context_text or not context_text.strip()):
        if language.lower() in ["hi", "hindi"]:
            return "अपलोड किए गए बीआईएस दस्तावेजों में इसका विश्वसनीय उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली।"
        elif language.lower() in ["mr", "marathi"]:
            return "अपलोड केलेल्या बीआयएस दस्तऐवजांमध्ये याचे विश्वसनीय उत्तर देण्यासाठी पुरेशी माहिती आढळली नाही."
        return "I could not find sufficient information in the uploaded BIS documents to answer this reliably."

    client = get_groq_client()
    primary_model = get_groq_model()

    lang_instruction = "Provide your answer in clear English."
    if language.lower() in ["hi", "hindi"]:
        lang_instruction = "Provide your complete answer in clear Hindi (हिंदी) language while keeping standard numbers (IS XXXX), clause numbers, numerical values, and units as they are."
    elif language.lower() in ["mr", "marathi"]:
        lang_instruction = "Provide your complete answer in clear Marathi (मराठी) language while keeping standard numbers (IS XXXX), clause numbers, numerical values, and units as they are."

    if is_conversational:
        system_prompt = (
            "You are an expert Bureau of Indian Standards (BIS) Standards Assistant.\n\n"
            f"Language Instruction: {lang_instruction}\n\n"
            "Rules:\n"
            "1. You are currently in a conversational state. Greet the user naturally or answer their meta-question (e.g. who are you).\n"
            "2. Do NOT mention specific Indian Standards (IS), document names, or clauses unless the user explicitly asks about them.\n"
            "3. Be polite, concise, and helpful."
        )
    else:
        system_prompt = (
            "You are a helpful, practical, and expert Bureau of Indian Standards (BIS) Assistant.\n\n"
            f"Language Instruction: {lang_instruction}\n\n"
            "Rules for Answering:\n"
            "1. For strict TECHNICAL specifications (limits, test conditions, clauses), you MUST use ONLY the provided document context. Do not guess or hallucinate IS numbers or test values.\n"
            "2. For GENERAL or ADMINISTRATIVE questions (e.g., 'how do I get certified?', 'explain this point', 'what does this mean?'), you SHOULD use your general industry knowledge to be as helpful and practical as possible.\n"
            "3. Conversational Memory: If the user asks an ambiguous follow-up (e.g., 'explain point 2', 'tell me more about the first one'), ALWAYS look at the immediate previous Assistant response in the chat history to understand what 'point 2' refers to. Do not assume they are talking about the newly provided document context unless explicitly stated.\n"
            "4. Be conversational, empathetic, and direct. Talk to the user like a senior engineering consultant advising a manufacturer. Avoid dry, robotic, or overly academic language.\n"
            "5. Format your answers beautifully using Markdown. Use short paragraphs, bold text for emphasis, and clear bullet points. Keep it highly readable and to the point.\n"
            "6. If a highly specific technical question cannot be answered by the context AND is beyond general knowledge, explicitly state: 'I could not find sufficient information in the uploaded BIS documents to answer this reliably.'"
        )

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        # Keep only the last 6 messages to prevent context dilution
        recent_history = chat_history[-6:]
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})

    # Structurally isolate the context from the question so the LLM doesn't confuse them
    user_prompt = (
        "--- NEWLY RETRIEVED DOCUMENT CONTEXT ---\n"
        f"{context_text}\n"
        "----------------------------------------\n\n"
        "--- USER'S NEXT QUESTION ---\n"
        f"{question}"
    )
    messages.append({"role": "user", "content": user_prompt})

    # Build model attempt order starting with primary configured model
    models_to_try = [primary_model] + [m for m in MODEL_CANDIDATES if m != primary_model]

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,  # Low temperature for factual precision
                max_tokens=1024
            )

            answer = response.choices[0].message.content.strip()
            if answer:
                return answer
        except Exception as e:
            last_error = e
            print(f"[LLM Warning] Groq call failed with model '{model_name}': {e}. Trying fallback...")
            continue

    print(f"[LLM Error] All Groq API model candidate calls failed: {last_error}")
    raise RuntimeError(f"Groq LLM generation error: {str(last_error)}")
