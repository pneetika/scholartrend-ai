from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def markdown_to_pdf(markdown_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    pdf.setTitle("ScholarTrend AI Research Report")
    width, height = LETTER
    x = 40
    y = height - 50

    for raw_line in markdown_text.splitlines():
        line = raw_line[:115]
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(x, y, line)
        y -= 14

    pdf.save()
    output_path.write_bytes(buffer.getvalue())
