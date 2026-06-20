import tempfile

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from xml.sax.saxutils import escape


class PDFExporter:

    def __init__(self):

        self.styles = getSampleStyleSheet()

    # ------------------------------------------------------------------
    # Escapes XML-unsafe characters ("&", "<", ">") so ReportLab's
    # Paragraph parser doesn't throw on financial text like "R&D" or
    # "EPS < 5". Newlines are converted to <br/> AFTER escaping so the
    # tag itself isn't double-escaped.
    # ------------------------------------------------------------------
    def _safe_text(self, text):

        if text is None or text == "":
            return "N/A"

        text = str(text)
        escaped = escape(text)
        escaped = escaped.replace("\n", "<br/>")
        return escaped

    def _build_sources_section(self, content, sources, label="Sources"):

        # FIX: defensive handling of malformed source entries.
        # If a chunk is missing "metadata", or metadata is missing
        # "source"/"page", this no longer raises a KeyError mid-export
        # and silently failing the whole PDF — it falls back to "Unknown".
        if not sources:
            content.append(
                Paragraph(
                    f"<b>{label}:</b> No sources retrieved.",
                    self.styles["BodyText"]
                )
            )
            return

        content.append(
            Paragraph(
                f"<b>{label}</b>",
                self.styles["Heading2"]
            )
        )

        seen = set()
        added_any = False

        for source in sources:

            if not isinstance(source, dict):
                continue

            metadata = source.get("metadata") or {}
            src_name = metadata.get("source", "Unknown")
            page = metadata.get("page", "N/A")

            key = (src_name, page)

            if key in seen:
                continue

            seen.add(key)
            added_any = True

            content.append(
                Paragraph(
                    self._safe_text(f"{src_name} - Page {page}"),
                    self.styles["BodyText"]
                )
            )

        if not added_any:
            content.append(
                Paragraph(
                    "No valid source entries to display.",
                    self.styles["BodyText"]
                )
            )

    def export_report(self, question, answer, sources):

        # FIX: wrapped the whole build in try/except. If ReportLab
        # still fails for any unanticipated reason (e.g. an extremely
        # long single line with no break points, malformed style),
        # this raises a clear RuntimeError instead of leaving a
        # half-written or zero-byte file behind, or letting Streamlit
        # show a raw traceback.
        tmp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
            prefix="finsight_report_"
        )
        output_path = tmp.name
        tmp.close()

        try:
            pdf = SimpleDocTemplate(output_path)
            content = []

            content.append(
                Paragraph("FinSight Research Report", self.styles["Title"])
            )
            content.append(Spacer(1, 12))

            content.append(
                Paragraph(
                    f"<b>Question:</b> {self._safe_text(question)}",
                    self.styles["BodyText"]
                )
            )
            content.append(Spacer(1, 12))

            content.append(
                Paragraph(
                    f"<b>Answer:</b><br/>{self._safe_text(answer)}",
                    self.styles["BodyText"]
                )
            )
            content.append(Spacer(1, 12))

            self._build_sources_section(content, sources, label="Sources")

            pdf.build(content)

        except Exception as e:
            raise RuntimeError(f"Failed to generate PDF report: {e}") from e

        return output_path

    def export_comparison_report(
        self,
        question,
        company_a,
        company_b,
        comparison_result,
        sources_a=None,
        sources_b=None
    ):

        tmp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
            prefix="finsight_comparison_"
        )
        output_path = tmp.name
        tmp.close()

        try:
            pdf = SimpleDocTemplate(output_path)
            content = []

            content.append(
                Paragraph("FinSight Comparison Report", self.styles["Title"])
            )
            content.append(Spacer(1, 12))

            content.append(
                Paragraph(
                    f"<b>Question:</b> {self._safe_text(question)}",
                    self.styles["BodyText"]
                )
            )
            content.append(Spacer(1, 6))

            content.append(
                Paragraph(
                    f"<b>Company A:</b> {self._safe_text(company_a)} "
                    f"&nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<b>Company B:</b> {self._safe_text(company_b)}",
                    self.styles["BodyText"]
                )
            )
            content.append(Spacer(1, 12))

            content.append(
                Paragraph(
                    f"<b>Comparison:</b><br/>{self._safe_text(comparison_result)}",
                    self.styles["BodyText"]
                )
            )
            content.append(Spacer(1, 12))

            self._build_sources_section(
                content,
                sources_a or [],
                label=f"Sources - {company_a}"
            )
            content.append(Spacer(1, 8))

            self._build_sources_section(
                content,
                sources_b or [],
                label=f"Sources - {company_b}"
            )

            pdf.build(content)

        except Exception as e:
            raise RuntimeError(
                f"Failed to generate comparison PDF report: {e}"
            ) from e

        return output_path