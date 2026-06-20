from sentence_transformers import SentenceTransformer


class Embedder:

    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def generate_embeddings(self, chunks):
        """
        Embeds a list of chunk dicts (each with a "text" key).
        Used at ingestion time for batches of document chunks.
        """

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            texts,
            show_progress_bar=True
        )

        return embeddings

    # ----------------------------------------------------------------
    # NEW: single entry point for embedding a raw query string.
    # Added so Retriever no longer reaches into self.embedder.model
    # directly. Both this method and generate_embeddings() now call
    # the same underlying self.model.encode(), guaranteeing query-time
    # and ingestion-time embeddings are produced identically. If any
    # preprocessing (normalization, different encode kwargs) is ever
    # added to one path, it must be added here too — having a single
    # named method makes that an explicit decision instead of an
    # accidental divergence.
    # ----------------------------------------------------------------
    def embed_query(self, query):

        embedding = self.model.encode(
            query,
            show_progress_bar=False
        )

        return embedding