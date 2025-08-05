from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from app.utils.detection import detect_and_annotate
from app.utils.analysis import analyse_defects_with_rag



def main():
    st.title("📸 Defects detection in PCB")

    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Pick a PCB Image",
            type=["png", "jpg", "jpeg"]
        )
        submitted = st.form_submit_button("Start detection")

    if submitted:
        if not uploaded_file:
            st.warning("❗ Choose an image")
        else:
            detections, annotated_buf = detect_and_annotate(uploaded_file)
            if  detections:
                with st.spinner("Analyzing PCB defects..."):
                        print(detections)
                        llm_answer = analyse_defects_with_rag(detections)
                st.success(f"‼️ Detection completed. PCB problems found!")
                st.image(
                    annotated_buf,
                    caption="Detections",
                    use_container_width=True
                )
                st.markdown("### Details (ChatGPT):")
                st.markdown(llm_answer)
            else:
                st.success(f"✅ Detection. No PCB problems found!")
if __name__ == "__main__":
    main()
