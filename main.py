import streamlit as st
from app.utils.detection import detect_and_annotate
import json

def process_llm(prediction_json: dict) -> str:
    """
    Ask chat GPT to classify the model PCB prediction.
    """

    promt = (
        "Eres un experto en calidad y ensamble electrónico, familiarizado con la norma IPC-A-610 (versión F). "
        "A continuación, recibirás información sobre defectos detectados en una imagen de una PCB: "
        + json.dumps(prediction_json)
    )

    # TODO: Process using OpenAPI or Claude Sonnet

    return ''

def main():
    st.title("📸 Defects detection in PCB")

    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Elija una imagen",
            type=["png", "jpg", "jpeg"]
        )
        submitted = st.form_submit_button("Iniciar detección")

    if submitted:
        if not uploaded_file:
            st.warning("❗ No se ha seleccionado ninguna imagen")
        else:
            detections, annotated_buf = detect_and_annotate(uploaded_file)
            st.success(f"✅ Detección completada!")
            st.image(
                annotated_buf,
                caption="Detecciones",
                use_container_width=True
            )
            # Aquí iría la respuesta del LLM estructurada.

if __name__ == "__main__":
    main()
