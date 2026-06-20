import chromadb


class ChromaStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="data/chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="financial_documents"
        )

    def add_documents(
        self,
        chunks,
        embeddings
    ):

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:

            ids.append(
                chunk["chunk_id"]
            )

            documents.append(
                chunk["text"]
            )

            metadatas.append(
                {
                    "doc_id": chunk["doc_id"],
                    "source": chunk["source"],
                    "page": chunk["page"]
                }
            )

        self.collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
)