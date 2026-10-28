import streamlit as st

from extractor import extract_text
from analyzer import analyze_job_description


st.set_page_config(
    page_title="JD Analytics",
    page_icon="📄",
    layout="wide"
)

st.title("📄 JD Analytics")
st.write(
    "Upload a job description to extract and analyze "
    "skills, qualifications, and responsibilities."
)

uploaded_file = st.file_uploader(
    "Upload a job description",
    type=["pdf", "docx"]
)

if uploaded_file is not None:

    if st.button("Analyze Job Description"):
        try:
            with st.spinner("Analyzing job description..."):

                # Extract text from the uploaded document
                jd_text = extract_text(
                    uploaded_file.name,
                    uploaded_file.getvalue()
                )

                # Analyze the extracted text using the LLM
                result = analyze_job_description(jd_text)

            st.success("Analysis completed successfully!")

            st.subheader("Extracted RADIX Skills")

            skills = result.skills

            if skills:
                st.dataframe(
                    [skill.model_dump() for skill in skills],
                    use_container_width=True
                )
            else:
                st.info("No relevant skills were identified.")

            # Allow the user to download the structured analysis
            st.download_button(
                label="Download Analysis as JSON",
                data=result.model_dump_json(indent=2),
                file_name="job_analysis.json",
                mime="application/json"
            )

        except Exception as exc:
            st.error(f"Analysis failed: {exc}")