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
        'NO.', 'Name', 'Phone', 'Cash', 'Main Orders', 'Addl. Orders', 'Hours', 'Work Date',
    ]
    orange_fill = PatternFill(start_color="F97316", end_color="F97316", fill_type="solid")
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = orange_fill
        cell.alignment = Alignment(horizontal='center')

    # Data rows
    for row_idx, invoice in enumerate(queryset, 2):
        ws.cell(row=row_idx, column=1, value=row_idx - 1)
        ws.cell(row=row_idx, column=2, value=f"{invoice.driver.first_name} {invoice.driver.last_name}")
        ws.cell(row=row_idx, column=3, value=invoice.driver.phone)
        ws.cell(row=row_idx, column=4, value=float(invoice.cash))
        ws.cell(row=row_idx, column=5, value=invoice.main_orders)
        ws.cell(row=row_idx, column=6, value=invoice.additional_orders)
        ws.cell(row=row_idx, column=7, value=float(invoice.hours))
        ws.cell(row=row_idx, column=8, value=str(invoice.specified_date))

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
        'NO.', 'Name', 'Phone', 'Cash', 'Main Orders', 'Addl. Orders', 'Hours', 'Work Date',
    ]
    orange_fill = PatternFill(start_color="F97316", end_color="F97316", fill_type="solid")
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = orange_fill
        cell.alignment = Alignment(horizontal='center')

    for row_idx, archive in enumerate(queryset, 2):
        ws.cell(row=row_idx, column=1, value=row_idx - 1)
        ws.cell(row=row_idx, column=2, value=archive.driver_name)
        ws.cell(row=row_idx, column=3, value=archive.driver.phone)
        ws.cell(row=row_idx, column=4, value=float(archive.cash))
        ws.cell(row=row_idx, column=5, value=archive.main_orders)
        ws.cell(row=row_idx, column=6, value=archive.additional_orders)
        ws.cell(row=row_idx, column=7, value=float(archive.hours))
        ws.cell(row=row_idx, column=8, value=str(archive.archive_date))

    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max(12, max_length + 2)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="archive_{label}.xlsx"'
    wb.save(response)
    return response

def generate_excel_template(model_type):
    """Generate a template .xlsx file for bulk upload."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Template"

    # Define headers per model
    if model_type == 'driver':
        headers = [
            'First Name', 'Last Name', 'Email', 'Phone', 'Civil ID Number',
            'Passport Number', 'Vehicle Plate Number', 'Vehicle Name', 'Company Name',
            'Contract Type', 'Vehicle Type'
        ]
    elif model_type == 'team':
        headers = [
            'First Name', 'Last Name', 'Email', 'Phone', 'Identification Number',
            'Passport', 'Role', 'Position', 'Base Salary KD'
        ]
    elif model_type == 'deduction':
        headers = [
            'Driver Email', 'Reason', 'Contracting Company', 
            'Contractor Deduction KD', 'Company Deduction KD'
        ]
    elif model_type == 'invoice':
        headers = [
            'NO.', 'Name', 'Phone', 'Cash', 'Main Orders', 'Addl. Orders', 'Hours', 'Work Date'
        ]
    else:
        headers = ['Data']

    orange_fill = PatternFill(start_color="F97316", end_color="F97316", fill_type="solid")
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = orange_fill
        cell.alignment = Alignment(horizontal='center')
        ws.column_dimensions[cell.column_letter].width = 20

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{model_type}_template.xlsx"'
    wb.save(response)
    return response


def import_from_excel(file, model_type, user):
    """Import data from uploaded Excel file."""
    from .models import Driver, Profile, DriverInvoice, Deduction
    from decimal import Decimal
    from datetime import date
    
    wb = openpyxl.load_workbook(file)
    ws = wb.active
    rows = list(ws.rows)
    
    if len(rows) < 2:
        return 0, "File is empty or missing data."

    headers = [cell.value for cell in rows[0]]
    count = 0
    errors = []

    for row_idx, row in enumerate(rows[1:], 2):
        data = {headers[i]: cell.value for i, cell in enumerate(row) if i < len(headers)}
        
        try:
            if model_type == 'driver':
                Driver.objects.create(
                    first_name=data.get('First Name'),
                    last_name=data.get('Last Name'),
                    email=data.get('Email'),
                    phone=data.get('Phone'),
                    civil_id_number=data.get('Civil ID Number'),
                    passport_number=data.get('Passport Number'),
                    vehicle_plate_number=data.get('Vehicle Plate Number'),
                    vehicle_name=data.get('Vehicle Name'),
                    company_name=data.get('Company Name', 'najmat'),
                    contract_type=data.get('Contract Type', 'talabat'),
                    vehicle_type=data.get('Vehicle Type', 'car'),
                    created_by=user.profile if hasattr(user, 'profile') else None
                )
            elif model_type == 'team':
                Profile.objects.create_user(
                    username=data.get('Email'),
                    email=data.get('Email'),
                    first_name=data.get('First Name'),
                    last_name=data.get('Last Name'),
                    phone=data.get('Phone', ''),
                    identification_number=data.get('Identification Number', ''),
                    passport=data.get('Passport', ''),
                    role=data.get('Role', 'employee'),
                    position=data.get('Position', 'Administrative'),
                    base_salary_kd=Decimal(str(data.get('Base Salary KD', 0) or 0)),
                    password='Password123!' # Default password
                )
            elif model_type == 'invoice':
                driver_phone = str(data.get('Phone', '')).strip()
                if not driver_phone:
                    errors.append(f"Row {row_idx}: Missing Phone number.")
                    continue
                
                try:
                    driver = Driver.objects.get(phone=driver_phone)
                except Driver.DoesNotExist:
                    errors.append(f"Row {row_idx}: Driver with phone {driver_phone} not found.")
                    continue
                
                DriverInvoice.objects.update_or_create(
                    driver=driver,
                    specified_date=data.get('Work Date') or date.today(),
                    defaults={
                        'cash': Decimal(str(data.get('Cash', 0) or 0)),
                        'main_orders': int(data.get('Main Orders', 0) or 0),
                        'additional_orders': int(data.get('Addl. Orders', 0) or 0),
                        'hours': Decimal(str(data.get('Hours', 0) or 0)),
                        'created_by': user.profile if hasattr(user, 'profile') else None
                    }
                )
            count += 1
        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    return count, errors
