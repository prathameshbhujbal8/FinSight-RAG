import os

from groq import Groq
from dotenv import load_dotenv


load_dotenv()


class GroqLLM:


    def __init__(self):

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )


    def generate_answer(
        self,
        question,
        retrieved_chunks
    ):

        # FIX: explicit empty-context guard. Without this, an empty
        # retrieval result still produces a prompt with a blank
        # CONTEXT section, which invites the LLM to guess rather
        # than correctly report that nothing was retrieved.
        if not retrieved_chunks:
            return (
                "No relevant information was retrieved from the "
                "documents for this question."
            )

        context = ""

        # FIX: every chunk is now tagged with its source filename and
        # page number BEFORE the chunk text, in the same block the LLM
        # reads. Previously sources were only printed separately in
        # app.py after generation — the LLM itself never saw which
        # chunk came from which source, so citation accuracy was not
        # actually grounded. This is the single biggest fix for
        # citation reliability.
        for chunk in retrieved_chunks:

            metadata = chunk["metadata"]

            context += (
                f"[Source: {metadata['source']}, "
                f"Page: {metadata['page']}]\n"
                + chunk["text"]
                + "\n\n"
            )


        prompt = f"""

You are FinSight, an AI investment research assistant.

Your job is to answer questions from financial documents.

Rules:
1. Use ONLY the provided context.
2. Do not hallucinate numbers.
3. If information is unavailable, say:
"Information not found in the provided documents."
4. Give concise analyst-style answers.
5. Each context block below is labeled with its source filename and
   page number in square brackets. When you state a fact, mention
   which source and page it came from, e.g. "(Source: filename.pdf,
   Page 12)".


CONTEXT:

{context}


QUESTION:

{question}


ANSWER:

"""

        # FIX: wrapped the API call in a try/except. An unhandled
        # exception here would crash a Streamlit app outright instead
        # of showing a usable error message.
        try:

            response = self.client.chat.completions.create(

                model="llama-3.1-8b-instant",

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.1
            )

            return (
                response
                .choices[0]
                .message
                .content
            )

        except Exception as e:

            return f"Error generating answer: {e}"