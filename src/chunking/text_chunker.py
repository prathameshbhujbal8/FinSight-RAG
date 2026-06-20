from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextChunker:

    def __init__(self):

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150
        )

    def chunk_pages(self, pages):

        chunks = []

        for page_data in pages:

            split_chunks = self.splitter.split_text(
                page_data["text"]
            )

            for idx, chunk in enumerate(split_chunks):

                chunks.append(
                    {
                        "chunk_id":
                        f"{page_data['doc_id']}_{page_data['page']}_{idx}",

                        "doc_id":
                        page_data["doc_id"],

                        "source":
                        page_data["source"],

                        "page":
                        page_data["page"],

                        "text":
                        chunk
                    }
                )

        return chunks