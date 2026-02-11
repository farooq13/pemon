import csv
from io import StringIO
from datetime import datetime
from django.http import StreamingHttpResponse
from django.db.models import Q

from .models import Transaction


class Echo:
    """
    An object that implements just the write method of the file-like interface.
    For streaming large CSV files.
    """
    def write(self, value):
        return value


def export_transactions_csv(queryset):
    """
    Export transactions to CSV format.
    
    """
    
    def iter_items(queryset):
        """Generator function to stream CSV rows."""
        
        # CSV Headers
        headers = [
            'Reference',
            'Date',
            'Time',
            'Type',
            'Amount',
            'Status',
            'Sender',
            'Recipient',
            'Description',
        ]
        
        # Yield header row
        yield headers
        
        # Yield data rows
        for txn in queryset.select_related('user', 'recipient').iterator():
            yield [
                txn.reference,
                txn.created_at.strftime('%Y-%m-%d'),
                txn.created_at.strftime('%H:%M:%S'),
                txn.get_transaction_type_display(),
                f"{txn.amount:.2f}",
                txn.get_status_display(),
                txn.user.email,
                txn.recipient.email if txn.recipient else '',
                txn.description or '',
            ]
    
    # Create CSV writer
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    
    # Generate CSV rows
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in iter_items(queryset)),
        content_type='text/csv'
    )
    
    # Set filename
    filename = f"transactions_{datetime.now().strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


