from docx import Document
from docx.shared import Pt

def text_to_docx(text: str, output_path: str):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)
    for paragraph_text in text.split('\n'):
        p = doc.add_paragraph(paragraph_text)
        if paragraph_text.startswith('#'):
            p.runs[0].bold = True
    doc.save(output_path)
