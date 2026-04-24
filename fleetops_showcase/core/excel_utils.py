import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font, PatternFill, Alignment


def export_invoices_excel(queryset, month_label):
    """Export DriverInvoice queryset to a formatted .xlsx file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Invoices {month_label}"

    # Header row with orange fill
    headers = [
        'Driver Name', 'Company', 'Contract', 'Date',
        'Cash (KWD)', 'Main Orders', 'Additional Orders',
        'Total Orders', 'Hours',
    ]
    orange_fill = PatternFill(start_color="F97316", end_color="F97316", fill_type="solid")
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = orange_fill
        cell.alignment = Alignment(horizontal='center')

    # Data rows
    for row_idx, invoice in enumerate(queryset, 2):
        ws.cell(row=row_idx, column=1, value=f"{invoice.driver.first_name} {invoice.driver.last_name}")
        ws.cell(row=row_idx, column=2, value=invoice.driver.get_company_name_display())
        ws.cell(row=row_idx, column=3, value=invoice.driver.get_contract_type_display())
        ws.cell(row=row_idx, column=4, value=str(invoice.specified_date))
        ws.cell(row=row_idx, column=5, value=float(invoice.cash))
        ws.cell(row=row_idx, column=6, value=invoice.main_orders)
        ws.cell(row=row_idx, column=7, value=invoice.additional_orders)
        ws.cell(row=row_idx, column=8, value=invoice.main_orders + invoice.additional_orders)
        ws.cell(row=row_idx, column=9, value=float(invoice.hours))

    # Auto-fit columns
    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max(12, max_length + 2)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="invoices_{month_label}.xlsx"'
    wb.save(response)
    return response


def export_archive_excel(queryset, label='archive'):
    """Export InvoiceArchive queryset to a formatted .xlsx file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Archive {label}"

    headers = [
        'Driver Name', 'Archive Date', 'Cash (KWD)',
        'Main Orders', 'Additional Orders', 'Total Orders', 'Hours',
    ]
    orange_fill = PatternFill(start_color="F97316", end_color="F97316", fill_type="solid")
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = orange_fill
        cell.alignment = Alignment(horizontal='center')

    for row_idx, archive in enumerate(queryset, 2):
        ws.cell(row=row_idx, column=1, value=archive.driver_name)
        ws.cell(row=row_idx, column=2, value=str(archive.archive_date))
        ws.cell(row=row_idx, column=3, value=float(archive.cash))
        ws.cell(row=row_idx, column=4, value=archive.main_orders)
        ws.cell(row=row_idx, column=5, value=archive.additional_orders)
        ws.cell(row=row_idx, column=6, value=archive.main_orders + archive.additional_orders)
        ws.cell(row=row_idx, column=7, value=float(archive.hours))

    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max(12, max_length + 2)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="archive_{label}.xlsx"'
    wb.save(response)
    return response
