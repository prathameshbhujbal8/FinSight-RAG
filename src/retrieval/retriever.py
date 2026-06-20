class Retriever:

    def __init__(
        self,
        chroma_store,
        embedder
    ):

        self.store = chroma_store
        self.embedder = embedder

    def retrieve(
        self,
        query,
        top_k=5,
        doc_filter=None,
        threshold=1.5
    ):

        query_embedding = (
            self.embedder
            .embed_query(query)
            .tolist()
        )

        where_filter = None

        if doc_filter:

            where_filter = {
                "doc_id": doc_filter
            }

        try:

            results = self.store.collection.query(

                query_embeddings=[
                    query_embedding
                ],

                n_results=top_k,

                where=where_filter,

                include=[
                    "documents",
                    "metadatas",
                    "distances"
                ]
            )

        except Exception as e:

            print(
                f"Retriever Error: {e}"
            )

            return []

        if (
            not results.get("documents")
            or
            not results["documents"][0]
        ):

            return []

        retrieved_chunks = []

        for i in range(
            len(results["documents"][0])
        ):

            distance = (
                results["distances"][0][i]
            )

            if distance <= threshold:

                retrieved_chunks.append(
                    {
                        "text":
                        results["documents"][0][i],

                        "metadata":
                        results["metadatas"][0][i],

                        "distance":
                        distance
                    }
                )

        return retrieved_chunks