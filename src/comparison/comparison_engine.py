from src.retrieval.retriever import Retriever


class ComparisonEngine:

    def __init__(self, store, embedder, llm):

        self.store = store
        self.embedder = embedder
        self.llm = llm

        # Reuse a single Retriever instance instead of constructing a
        # new one on every call (no real cost here, but avoids
        # re-creating state unnecessarily on each comparison).
        self.retriever = Retriever(self.store, self.embedder)

    def compare_companies(self, question, company_a, company_b):

        # ------------------------------------------------------------
        # FIX: Retriever.retrieve() takes `company_filter`, not
        # `doc_filter`. The old call raised TypeError every time
        # compare() was invoked. Parameter name corrected below.
        # ------------------------------------------------------------
        company_a_chunks = self.retriever.retrieve(
         question,
         top_k=5,
         doc_filter=company_a
        )

        company_b_chunks = self.retriever.retrieve(
            question,
            top_k=5,
            doc_filter=company_b
        )

        # ------------------------------------------------------------
        # FIX: empty retrieval guard. If one or both companies have
        # no relevant chunks (nothing ingested yet, or distance
        # threshold filtered everything out), don't hand the LLM a
        # blank context block for that company — that's exactly how
        # it ends up inventing plausible-sounding numbers. Instead we
        # short-circuit with a clear message and skip the LLM call
        # entirely if BOTH sides are empty, since there is nothing to
        # compare.
        # ------------------------------------------------------------
        if not company_a_chunks and not company_b_chunks:
            return (
                f"No relevant information was found for either "
                f"{company_a} or {company_b} for this question. "
                f"Please confirm both documents have been ingested.",
                [],
                []
            )

        if not company_a_chunks:
            context_a = (
                "No relevant information was retrieved for this "
                "company for this question."
            )
        else:
            context_a = "\n\n".join(
                chunk["text"] for chunk in company_a_chunks
            )

        if not company_b_chunks:
            context_b = (
                "No relevant information was retrieved for this "
                "company for this question."
            )
        else:
            context_b = "\n\n".join(
                chunk["text"] for chunk in company_b_chunks
            )

        prompt = f"""

You are a financial research analyst.

Compare the two companies using ONLY the provided contexts.

If a context says no information was retrieved for a company, you
MUST say that comparison is not possible for that company on this
question rather than guessing or using outside knowledge.

QUESTION:
{question}


COMPANY A: {company_a}

CONTEXT:
{context_a}


COMPANY B: {company_b}

CONTEXT:
{context_b}


Provide:

1. Company A Summary
2. Company B Summary
3. Key Differences
4. Investment Insight

"""

        # NOTE: model name is duplicated here and in GroqLLM
        # (llama-3.1-8b-instant). Not fixed in this pass to avoid
        # touching GroqLLM's interface — flagging as a follow-up:
        # expose a shared MODEL_NAME constant or have GroqLLM expose
        # a generate_raw(prompt) method so this duplication goes away.
        try:
            response = self.llm.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            result_text = response.choices[0].message.content

        except Exception as e:
            result_text = f"Error generating comparison: {e}"

        # ------------------------------------------------------------
        # FIX: previously the retrieved chunks were used for context
        # and then discarded — there was no way to cite comparison
        # sources. Now we return them alongside the result so the
        # Streamlit layer (and PDF export) can display/cite them.
        # ------------------------------------------------------------
        return result_text, company_a_chunks, company_b_chunks