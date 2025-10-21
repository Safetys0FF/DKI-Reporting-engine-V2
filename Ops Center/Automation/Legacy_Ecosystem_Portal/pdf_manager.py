# pdf_manager.py
# Handles PDF export and basic customization for report generation

from fpdf import FPDF
import os
from datetime import datetime

class PDFManager:
    def __init__(self, output_dir="./cases"):
        self.output_dir = output_dir

    def export_report(self, case_id, report_data):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"Case Report: {case_id}", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Generated: {datetime.utcnow().isoformat()}", ln=True, align='C')
        pdf.ln(10)

        for section_id, content in report_data.items():
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Section {section_id}", ln=True)
            pdf.set_font("Arial", '', 12)
            body = content.get("narrative_text") or content.get("body") or "[No content]"
            for line in body.splitlines():
                pdf.multi_cell(0, 10, line)
            pdf.ln(5)

        output_path = os.path.join(self.output_dir, case_id, "report.pdf")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf.output(output_path)
        return output_path

    def export_custom_cover(self, case_id, metadata):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 10, txt="Investigation Report", ln=True, align='C')

        pdf.set_font("Arial", '', 14)
        pdf.ln(20)
        for key, value in metadata.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

        cover_path = os.path.join(self.output_dir, case_id, "cover_page.pdf")
        os.makedirs(os.path.dirname(cover_path), exist_ok=True)
        pdf.output(cover_path)
        return cover_path
