from src.ingestion.pdf_parser import PDFParser
from src.chunking.text_chunker import TextChunker
from src.embeddings.embedder import Embedder
from src.vectordb.chroma_store import ChromaStore
from src.retrieval.retriever import Retriever
from src.llm.groq_llm import GroqLLM



# ===============================
# PHASE 1: PDF INGESTION
# ===============================

pdf_path = "data/raw_pdfs/infosys_annual_report_2025.pdf"


print("\nLoading PDF...\n")

parser = PDFParser(pdf_path)

pages = parser.extract_pages()


print(
    f"Pages Extracted: {len(pages)}"
)



# ===============================
# PHASE 2: CHUNKING
# ===============================


print("\nCreating Chunks...\n")


chunker = TextChunker()


chunks = chunker.chunk_pages(
    pages
)


print(
    f"Chunks Created: {len(chunks)}"
)



print("\nSample Chunk:\n")

print(
    chunks[0]
)



# ===============================
# PHASE 3: EMBEDDINGS
# ===============================


print(
    "\nGenerating Embeddings...\n"
)


embedder = Embedder()


# FIX: removed chunks[:50] truncation.
# Full document is now embedded and stored, not just the first 50 chunks.
all_chunks = chunks


embeddings = embedder.generate_embeddings(
    all_chunks
)



# ===============================
# PHASE 4: CHROMADB STORAGE
# ===============================


print(
    "\nStoring In ChromaDB...\n"
)


store = ChromaStore()


store.add_documents(
    all_chunks,
    embeddings
)


print(
    "Stored Successfully In ChromaDB"
)



# ===============================
# PHASE 5: RETRIEVAL
# ===============================


retriever = Retriever(
    store,
    embedder
)



question = (
    "What is Infosys AI strategy?"
)



print(
    "\nSearching Relevant Documents...\n"
)


# FIX: retrieve() now returns only chunks that pass the distance
# threshold. If nothing passes, retrieved_chunks will be an empty list
# and GroqLLM.generate_answer() handles that case explicitly.
#
# Optional doc filtering is available via company_filter, e.g.:
# retriever.retrieve(question, top_k=5, company_filter="infosys_annual_report_2025")
retrieved_chunks = retriever.retrieve(
    question,
    top_k=5
)



print(
    "\nRetrieved Results\n"
)



if not retrieved_chunks:
    print("No chunks passed the relevance threshold.")

for chunk in retrieved_chunks:

    print(
        chunk["metadata"]
    )


    print(
        chunk["text"][:300]
    )


    print(
        "----------------"
    )



# ===============================
# PHASE 6: LLM GENERATION
# ===============================


print(
    "\nGenerating Final Answer...\n"
)


llm = GroqLLM()



answer = llm.generate_answer(
    question,
    retrieved_chunks
)



print(
    "\n========== FINANCE ANSWER ==========\n"
)


print(answer)



print(
    "\n========== SOURCES ==========\n"
)



for chunk in retrieved_chunks:

    metadata = chunk["metadata"]


    print(
        f"""
Source: {metadata['source']}
Page: {metadata['page']}
"""
    )