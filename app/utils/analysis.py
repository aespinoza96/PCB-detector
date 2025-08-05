import os
import json
from typing import Any, Dict
import openai

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
)


if not OPENAI_API_KEY:
    raise RuntimeError(
        "🔑 OPENAI_API_KEY is missing. Set it as an env var or in st.secrets."
    )

client = openai.OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_QA = (
    "You are an expert in electronic-assembly quality assurance and IPC-A-610F. "
    "Analyse detected PCB defects and suggest corrective actions."
)

TABLE_INSTRUCTIONS = (
    "For each defect provide: **reference**, **defect_type (IPC-A-610F)**, "
    "**severity (Class 1/2/3)**. Answer as a **GitHub-flavoured Markdown table** "
    "with headers."
)

def _build_user_prompt(prediction_json: Dict[str, Any]) -> str:
    pretty = json.dumps(prediction_json, ensure_ascii=False, indent=2)
    return f"PCB defects (JSON):\n```json\n{pretty}\n```\n\n{TABLE_INSTRUCTIONS}"

def _format_sources(results):
    """Return XML-ish wrapper expected by the RAG prompt."""
    formatted_results = ''
    for result in results.data:
        formatted_result = f"<result file_id='{result.file_id}' file_name='{result.file_name}'>"
        for part in result.content:
            formatted_result += f"<content>{part.text}</content>"
        formatted_results += formatted_result + "</result>"
    return f"<sources>{formatted_results}</sources>"

def analyse_defects_with_chat(prediction_json: dict) -> str:
    """
    One-shot GPT call (no retrieval) that returns a Markdown table.
    """

    if not prediction_json:
        raise ValueError("prediction_json is empty")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_QA},
            {"role": "user",   "content": _build_user_prompt(prediction_json)},
        ],
        temperature=0.2,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()
    
def analyse_defects_with_rag(prediction_json: dict) -> str:
    """
    GPT call **with** vector-store retrieval (RAG).
    Returns Markdown table enriched with citations.
    """
    
    if not prediction_json:
        raise ValueError("prediction_json is empty")

    
    query = _build_user_prompt(prediction_json)

    results = client.vector_stores.search(
        vector_store_id='vs_689153891e14819198a310519b022630',
        query=query
    )

    formatted_results = ''
    for result in results.data:
        formatted_result = f"<result file_id='{result.file_id}' file_name='{result.filename}'>"
        for part in result.content:
            formatted_result += f"<content>{part.text}</content>"
        formatted_results += formatted_result + "</result>"
    formatted_results = f"<sources>{formatted_results}</sources>"
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",    "content": "Produce a concise answer to the query based on the provided sources."},
            {"role": "assistant", "content": formatted_results},
            {"role": "user",      "content": query},
        ]
    )
    return completion.choices[0].message.content.strip()