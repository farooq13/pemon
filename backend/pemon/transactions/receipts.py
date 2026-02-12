"""
Transaction Receipt Generation

Generates PDF receipts for transactions.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from django.conf import settings
from transactions.models import Transaction


def generate_transaction_receipt(transaction: Transaction) -> BytesIO:
    """
    Generate a PDF receipt for a transaction.
    
    Args:
        transaction: Transaction object
        
    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E40AF'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    # Company Header
    elements.append(Paragraph("PEMON", title_style))
    elements.append(Paragraph("Digital Wallet", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Transaction Receipt Title
    receipt_title = Paragraph(
        f"<b>TRANSACTION RECEIPT</b>",
        ParagraphStyle(
            'ReceiptTitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    )
    elements.append(receipt_title)
    
    # Status Badge
    status_color = {
        'COMPLETED': colors.green,
        'PENDING': colors.orange,
        'FAILED': colors.red,
        'REVERSED': colors.grey
    }.get(transaction.status, colors.grey)
    
    status_para = Paragraph(
        f"<b>{transaction.get_status_display()}</b>",
        ParagraphStyle(
            'Status',
            parent=styles['Normal'],
            fontSize=12,
            textColor=status_color,
            alignment=TA_CENTER,
            spaceAfter=20
        )
    )
    elements.append(status_para)
    elements.append(Spacer(1, 0.2*inch))
    
    # Transaction Details Table
    details_data = [
        ['Reference Number:', transaction.reference],
        ['Transaction Type:', transaction.get_transaction_type_display()],
        ['Amount:', f"₦{transaction.amount:,.2f}"],
        ['Date & Time:', transaction.created_at.strftime('%B %d, %Y %I:%M %p')],
    ]
    
    # Add sender/recipient info if transfer
    if transaction.transaction_type == 'TRANSFER':
        details_data.extend([
            ['From:', transaction.user.email],
            ['To:', transaction.recipient.email if transaction.recipient else 'N/A'],
        ])
    else:
        details_data.append(['User:', transaction.user.email])
    
    if transaction.description:
        details_data.append(['Description:', transaction.description])
    
    # Create table
    details_table = Table(details_data, colWidths=[2*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Amount Highlight Box
    if transaction.status == 'COMPLETED':
        amount_data = [[f"₦{transaction.amount:,.2f}"]]
        amount_table = Table(amount_data, colWidths=[6*inch])
        amount_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 24),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#059669')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#D1FAE5')),
            ('BOX', (0, 0), (0, 0), 2, colors.HexColor('#059669')),
            ('TOPPADDING', (0, 0), (0, 0), 15),
            ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ]))
        elements.append(amount_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    
    footer_text = f"""
    <para align="center">
    <font size="9" color="#9CA3AF">
    This is a computer-generated receipt and does not require a signature.<br/>
    For inquiries, contact support@pemon.ng<br/>
    Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    </font>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF from buffer
    buffer.seek(0)
    return buffer


def generate_receipt_html(transaction: Transaction) -> str:
    """
    Generate an HTML receipt for a transaction.
    
    Useful for email or web display.
    
    Args:
        transaction: Transaction object
        
    Returns:
        str: HTML receipt
    """
    status_colors = {
        'COMPLETED': '#059669',
        'PENDING': '#F59E0B',
        'FAILED': '#DC2626',
        'REVERSED': '#6B7280'
    }
    
    status_bg_colors = {
        'COMPLETED': '#D1FAE5',
        'PENDING': '#FEF3C7',
        'FAILED': '#FEE2E2',
        'REVERSED': '#F3F4F6'
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transaction Receipt - {transaction.reference}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #1F2937;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #F9FAFB;
            }}
            .receipt {{
                background: white;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: bold;
                color: #1E40AF;
                margin-bottom: 5px;
            }}
            .subtitle {{
                color: #6B7280;
                font-size: 14px;
            }}
            .receipt-title {{
                font-size: 20px;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
            }}
            .status {{
                display: inline-block;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                background-color: {status_bg_colors.get(transaction.status, '#F3F4F6')};
                color: {status_colors.get(transaction.status, '#6B7280')};
                margin-bottom: 30px;
            }}
            .details {{
                margin: 30px 0;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 12px 0;
                border-bottom: 1px solid #E5E7EB;
            }}
            .detail-label {{
                color: #6B7280;
                font-weight: 500;
            }}
            .detail-value {{
                color: #1F2937;
                font-weight: 600;
                text-align: right;
            }}
            .amount-box {{
                text-align: center;
                padding: 30px;
                background-color: #D1FAE5;
                border: 2px solid #059669;
                border-radius: 12px;
                margin: 30px 0;
            }}
            .amount {{
                font-size: 36px;
                font-weight: bold;
                color: #059669;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #E5E7EB;
                color: #9CA3AF;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="receipt">
            <div class="header">
                <div class="logo">PEMON</div>
                <div class="subtitle">Digital Wallet</div>
            </div>
            
            <div class="receipt-title">TRANSACTION RECEIPT</div>
            
            <div style="text-align: center;">
                <span class="status">{transaction.get_status_display()}</span>
            </div>
            
            <div class="details">
                <div class="detail-row">
                    <span class="detail-label">Reference Number</span>
                    <span class="detail-value">{transaction.reference}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Transaction Type</span>
                    <span class="detail-value">{transaction.get_transaction_type_display()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Amount</span>
                    <span class="detail-value">₦{transaction.amount:,.2f}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Date & Time</span>
                    <span class="detail-value">{transaction.created_at.strftime('%B %d, %Y %I:%M %p')}</span>
                </div>
    """
    
    if transaction.transaction_type == 'TRANSFER':
        html += f"""
                <div class="detail-row">
                    <span class="detail-label">From</span>
                    <span class="detail-value">{transaction.user.email}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">To</span>
                    <span class="detail-value">{transaction.recipient.email if transaction.recipient else 'N/A'}</span>
                </div>
        """
    else:
        html += f"""
                <div class="detail-row">
                    <span class="detail-label">User</span>
                    <span class="detail-value">{transaction.user.email}</span>
                </div>
        """
    
    if transaction.description:
        html += f"""
                <div class="detail-row">
                    <span class="detail-label">Description</span>
                    <span class="detail-value">{transaction.description}</span>
                </div>
        """
    
    html += """
            </div>
    """
    
    if transaction.status == 'COMPLETED':
        html += f"""
            <div class="amount-box">
                <div class="amount">₦{transaction.amount:,.2f}</div>
            </div>
        """
    
    html += f"""
            <div class="footer">
                This is a computer-generated receipt and does not require a signature.<br>
                For inquiries, contact support@pemon.ng<br>
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html