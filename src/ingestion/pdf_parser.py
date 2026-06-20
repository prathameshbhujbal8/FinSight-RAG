import fitz
from pathlib import Path

from src.ingestion.text_cleaner import clean_text


class PDFParser:

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def extract_pages(self):

        document = fitz.open(self.pdf_path)

        pages = []

        source_name = Path(self.pdf_path).name

        doc_id = source_name.replace(".pdf", "")

        for page_num in range(len(document)):

            page = document.load_page(page_num)

            raw_text = page.get_text()

            cleaned_text = clean_text(raw_text)

            pages.append(
                {
                    "doc_id": doc_id,
                    "page": page_num + 1,
                    "source": source_name,
                    "text": cleaned_text
                }
            )

        document.close()

        return pages