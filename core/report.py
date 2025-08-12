# core/report.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


def create_pdf_report(filename, original, rewritten, plagiarism_score, web_matches=None, faiss_matches=None):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    flowables = []

    # Заголовок
    flowables.append(Paragraph("Отчёт AntiPlagiarism Pro", styles['Title']))
    flowables.append(Spacer(1, 0.3*inch))

    # Уникальность
    color = colors.green if plagiarism_score > 70 else colors.orange if plagiarism_score > 40 else colors.red
    unique_style = ParagraphStyle(
        'Unique', parent=styles['Normal'], textColor=color, fontSize=14)
    flowables.append(Paragraph(
        f"<b>Уровень уникальности:</b> {plagiarism_score:.1f}%", unique_style))
    flowables.append(Spacer(1, 0.2*inch))

    # Оригинал
    flowables.append(
        Paragraph("<b>Оригинальный текст:</b>", styles['Heading3']))
    for para in original.split('\n')[:10]:
        if para.strip():
            flowables.append(Paragraph(f"• {para.strip()}", styles['Normal']))
    flowables.append(Spacer(1, 0.2*inch))

    # Совпадения из интернета
    if web_matches:
        flowables.append(
            Paragraph("<b>Найдено в интернете:</b>", styles['Heading3']))
        data = [["№", "Фрагмент", "Ссылка", "Схожесть"]]
        for i, m in enumerate(web_matches[:5], 1):
            data.append([
                str(i),
                m['text'][:60] + "...",
                f"<a href='{m['link']}'>Перейти</a>",
                f"{m['similarity']:.2f}"
            ])
        table = Table(data, colWidths=[0.5*inch, 3*inch, 1.5*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        flowables.append(table)
        flowables.append(Spacer(1, 0.2*inch))

    # Совпадения из локальной базы
    if faiss_matches:
        flowables.append(
            Paragraph("<b>Найдено в локальной базе:</b>", styles['Heading3']))
        for m in faiss_matches[:3]:
            flowables.append(Paragraph(
                f"• <i>{m['text']}</i> <b>({m['similarity']:.2f})</b> — из: {m['title']}",
                styles['Normal']
            ))
        flowables.append(Spacer(1, 0.2*inch))

    # Перефразированный текст
    flowables.append(
        Paragraph("<b>Уникальная версия:</b>", styles['Heading3']))
    for para in rewritten.split('\n'):
        if para.strip():
            flowables.append(Paragraph(para.strip(), styles['Normal']))

    doc.build(flowables)
