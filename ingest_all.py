import os

from src.pipeline.rag_pipeline import RAGPipeline


pipeline = RAGPipeline()


pdf_folder = "data/raw_pdfs"


for file in os.listdir(pdf_folder):

    if file.endswith(".pdf"):

        pdf_path = os.path.join(
            pdf_folder,
            file
        )

        print(
            f"\nProcessing {file} ..."
        )

        chunks = pipeline.ingest_pdf(
            pdf_path,
            file
        )

        print(
            f"{chunks} chunks stored."
        )