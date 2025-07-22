import os
import json
import openai

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
)


if not OPENAI_API_KEY:
    raise RuntimeError(
        "🔑 OPENAI_API_KEY is missing. Set it as an env var or in st.secrets."
    )

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def process_llm(prediction_json: dict) -> str:
    """
    Send `prediction_json` (your YOLO detections) to ChatGPT and return the reply
    as plain text. If you need a structured answer, ask the model to answer in
    JSON (see the prompt example below).
    """
    system_prompt = (
        "You are an expert in quality assurance for electronic assemblies "
        "and you are familiar with the IPC-A-610F standard. Analyze the detected defects and "
        "return a brief classification and suggested corrective action from user input.\n"
        ""
    )

    user_prompt = (
        "Defectos detectados en la PCB (formato JSON):\n"
        f"{json.dumps(prediction_json, ensure_ascii=False, indent=2)}\n\n"
        "Classifies each defect by indicating: component reference, defect "
        "type (according to IPC-A-610F), and severity (Class 1, 2, or 3). "
        "Returns the response as a table in Markdown."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

    except openai.OpenAIError as exc:
        # You might want richer error handling/logging here
        return f"⚠️ Error al consultar ChatGPT: {exc}"