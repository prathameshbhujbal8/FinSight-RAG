from src.ingestion.pdf_parser import PDFParser
from src.chunking.text_chunker import TextChunker
from src.embeddings.embedder import Embedder
from src.vectordb.chroma_store import ChromaStore
from src.retrieval.retriever import Retriever
from src.llm.groq_llm import GroqLLM
from src.comparison.comparison_engine import ComparisonEngine


class RAGPipeline:

    def __init__(self):

        self.embedder = Embedder()
        self.store = ChromaStore()
        self.llm = GroqLLM()

        self.comparison_engine = ComparisonEngine(
            self.store,
            self.embedder,
            self.llm
        )

    def ingest_pdf(self, pdf_path, original_filename=None):

        parser = PDFParser(pdf_path)
        pages = parser.extract_pages()

        chunker = TextChunker()
        chunks = chunker.chunk_pages(pages)

        if original_filename:
            for chunk in chunks:
                chunk["source"] = original_filename

        embeddings = self.embedder.generate_embeddings(chunks)

        self.store.add_documents(chunks, embeddings)

        return len(chunks)

    def ask(self, question):

        retriever = Retriever(self.store, self.embedder)

        chunks = retriever.retrieve(question)

        answer = self.llm.generate_answer(question, chunks)

        return answer, chunks

    def compare(self, question, company_a, company_b):

        # FIX: compare_companies() now returns a 3-tuple
        # (result_text, sources_a, sources_b) instead of just text,
        # so the Streamlit layer can show/export comparison sources.
        # This pass-through keeps RAGPipeline.compare() the single
        # entry point streamlit_app.py needs to call.
        return self.comparison_engine.compare_companies(
            question,
            company_a,
            company_b
        )