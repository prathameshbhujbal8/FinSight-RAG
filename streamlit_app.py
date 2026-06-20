import os
import streamlit as st
import tempfile

from src.pipeline.rag_pipeline import RAGPipeline
from src.analytics.query_logger import QueryLogger
from src.export.pdf_exporter import PDFExporter

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="FinSight RAG",
    layout="wide"
)

st.title("📊 FinSight RAG")
st.write("AI Investment Research Assistant")


# =====================================
# STARTUP CHECKS
# =====================================

# FIX: fail fast and clearly if GROQ_API_KEY is missing, instead of
# letting it surface deep inside the first LLM call as a confusing
# stack trace mid-demo.
if not os.environ.get("GROQ_API_KEY") and "GROQ_API_KEY" not in st.secrets:
    st.error(
        "GROQ_API_KEY is not configured. "
        "Set it as an environment variable or in Streamlit secrets "
        "before using this app."
    )
    st.stop()


# =====================================
# LOAD PIPELINE
# =====================================

@st.cache_resource
def load_pipeline():
    return RAGPipeline()


pipeline = load_pipeline()
logger = QueryLogger()
exporter = PDFExporter()


# =====================================
# PDF UPLOAD
# =====================================

uploaded_file = st.file_uploader(
    "Upload Financial PDF",
    type=["pdf"]
)


if uploaded_file:

    # FIX: basic size guard before writing to disk / processing.
    # Prevents a very large upload from hanging the app for minutes
    # with no feedback beyond a spinner.
    MAX_FILE_SIZE_MB = 25
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(
            f"File is {file_size_mb:.1f} MB, which exceeds the "
            f"{MAX_FILE_SIZE_MB} MB limit. Please upload a smaller PDF."
        )

    else:

        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

        except Exception as e:
            st.error(f"Failed to save uploaded file: {e}")

        if tmp_path and st.button("Process Document"):

            # FIX: the actual processing call is now wrapped in
            # try/except. A corrupted PDF, an encrypted PDF, or a
            # PDF with no extractable text previously raised an
            # unhandled exception here and crashed the app.
            try:
                with st.spinner("Processing PDF..."):

                    chunk_count = pipeline.ingest_pdf(
                        tmp_path,
                        uploaded_file.name
                    )

                if chunk_count == 0:
                    st.warning(
                        "No text could be extracted from this PDF. "
                        "It may be a scanned/image-only document."
                    )
                else:
                    st.success(f"Processed {chunk_count} chunks")

            except Exception as e:
                st.error(
                    f"Failed to process '{uploaded_file.name}': {e}\n\n"
                    "This can happen with corrupted, encrypted, or "
                    "scanned PDFs. Try a different file."
                )

            finally:
                # Clean up the temp upload file regardless of outcome.
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass


# =====================================
# QUESTION INPUT
# =====================================

question = st.text_input("Ask a financial question")


if st.button("Generate Answer"):

    if question:

        try:
            with st.spinner("Researching..."):

                answer, sources = pipeline.ask(question)

            st.session_state["last_question"] = question
            st.session_state["last_answer"] = answer
            st.session_state["last_sources"] = sources

            st.session_state.pop("last_comparison", None)

            # FIX: logging failure no longer blocks the answer from
            # being displayed. Previously a logger error (e.g. DB
            # locked, disk full) happened before the answer render,
            # meaning a logging bug could hide a perfectly good answer.
            document = "Unknown"
            if sources:
                document = sources[0]["metadata"].get("source", "Unknown")

            try:
                logger.log_query(question, document)
            except Exception as log_err:
                st.caption(f"(Query logging failed: {log_err})")

            st.subheader("Answer")
            st.write(answer)

            st.subheader("Sources")

            if not sources:
                st.info("No sources were retrieved for this answer.")
            else:
                seen = set()

                for source in sources:

                    metadata = source.get("metadata", {})
                    key = (metadata.get("source"), metadata.get("page"))

                    if key not in seen:

                        seen.add(key)

                        st.write(
                            f"📄 {metadata.get('source', 'Unknown')}  \n"
                            f"Page: {metadata.get('page', 'N/A')}"
                        )
                        st.divider()

        except Exception as e:
            st.error(f"Failed to generate answer: {e}")

    else:
        st.warning("Please enter a question.")


# =====================================
# EXPORT - NORMAL Q&A
# =====================================

st.subheader("📄 Export Report")

if "last_answer" in st.session_state:

    if st.button("Generate PDF Report"):

        try:
            pdf_path = exporter.export_report(
                st.session_state["last_question"],
                st.session_state["last_answer"],
                st.session_state["last_sources"]
            )

            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="Download PDF",
                    data=file,
                    file_name="FinSight_Report.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"PDF export failed: {e}")

else:
    st.caption("Ask a question first to enable export.")


# =====================================
# ANALYTICS DASHBOARD
# =====================================

st.divider()
st.header("📈 Analytics Dashboard")

try:

    total_queries = logger.get_total_queries()
    document_count = logger.get_document_count()
    most_queried = logger.get_most_queried_document()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Queries", total_queries)

    with col2:
        st.metric("Documents Processed", document_count)

    with col3:
        if most_queried:
            st.metric("Most Queried Document", most_queried[0])
        else:
            st.metric("Most Queried Document", "N/A")

    st.subheader("🕒 Recent Questions")

    recent_queries = logger.get_recent_queries()

    if recent_queries:
        for q, timestamp in recent_queries:
            st.write(f"• {q}")
            st.caption(timestamp)
    else:
        st.info("No queries logged yet.")

except Exception as e:
    st.error(f"Analytics Error: {e}")


# =====================================
# COMPANY COMPARISON
# =====================================

st.divider()
st.header("📊 Company Comparison")

comparison_question = st.text_input("Comparison Question")

company_a = st.selectbox(
    "Company A",
    ["infosys_annual_report_2025", "tcs_annual_report_2025"]
)

company_b = st.selectbox(
    "Company B",
    ["tcs_annual_report_2025", "infosys_annual_report_2025"]
)

if st.button("Compare Companies"):

    if not comparison_question:
        st.warning("Please enter a comparison question.")

    elif company_a == company_b:
        st.warning("Please select two different companies to compare.")

    else:

        try:
            with st.spinner("Comparing Companies..."):

                comparison_result, sources_a, sources_b = pipeline.compare(
                    comparison_question,
                    company_a,
                    company_b
                )

            st.session_state["last_comparison"] = {
                "question": comparison_question,
                "company_a": company_a,
                "company_b": company_b,
                "result": comparison_result,
                "sources_a": sources_a,
                "sources_b": sources_b
            }

            try:
                logger.log_query(
                    comparison_question,
                    f"{company_a} vs {company_b}"
                )
            except Exception as log_err:
                st.caption(f"(Query logging failed: {log_err})")

            st.subheader("Comparison Result")
            st.write(comparison_result)

            if not sources_a and not sources_b:
                st.info(
                    "No sources were retrieved for either company "
                    "for this question."
                )
            else:
                col_a, col_b = st.columns(2)

                with col_a:
                    st.caption(f"Sources - {company_a}")
                    if not sources_a:
                        st.write("No sources retrieved.")
                    else:
                        seen_a = set()
                        for source in sources_a:
                            meta = source.get("metadata", {})
                            key = (meta.get("source"), meta.get("page"))
                            if key not in seen_a:
                                seen_a.add(key)
                                st.write(
                                    f"📄 {meta.get('source', 'Unknown')} "
                                    f"— p.{meta.get('page', 'N/A')}"
                                )

                with col_b:
                    st.caption(f"Sources - {company_b}")
                    if not sources_b:
                        st.write("No sources retrieved.")
                    else:
                        seen_b = set()
                        for source in sources_b:
                            meta = source.get("metadata", {})
                            key = (meta.get("source"), meta.get("page"))
                            if key not in seen_b:
                                seen_b.add(key)
                                st.write(
                                    f"📄 {meta.get('source', 'Unknown')} "
                                    f"— p.{meta.get('page', 'N/A')}"
                                )

        except Exception as e:
            st.error(f"Comparison failed: {e}")


# =====================================
# EXPORT - COMPARISON
# =====================================

if "last_comparison" in st.session_state:

    st.subheader("📄 Export Comparison Report")

    if st.button("Generate Comparison PDF"):

        try:
            comp = st.session_state["last_comparison"]

            pdf_path = exporter.export_comparison_report(
                comp["question"],
                comp["company_a"],
                comp["company_b"],
                comp["result"],
                sources_a=comp["sources_a"],
                sources_b=comp["sources_b"]
            )

            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="Download Comparison PDF",
                    data=file,
                    file_name="FinSight_Comparison_Report.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Comparison PDF export failed: {e}")