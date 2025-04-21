import re
from decimal import Decimal
from django.db import transaction
from .models import PayrollRun, Payslip, PayslipComponent, EmployeeSalaryStructure, SalaryComponent
import calendar
import logging

# Set up logging
logger = logging.getLogger(__name__)


def process_payroll(payroll_run_id):
    payroll_run = PayrollRun.objects.get(id=payroll_run_id)
    employees = payroll_run.get_employees()  # Use the updated method from PayrollRun

    with transaction.atomic():
        for employee in employees:
            # Get employee's salary structure
            salary_structures = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)

            # Skip if no salary structure is defined
            if not salary_structures.exists():
                logger.warning(f"Skipping employee {employee} - No active salary structure defined.")
                continue  # Skip this employee

            # Initialize totals
            total_additions = Decimal('0.00')
            total_deductions = Decimal('0.00')
            basic_salary = None

            # Create payslip
            payslip = Payslip.objects.create(
                payroll_run=payroll_run,
                employee=employee,
                status='pending'
            )

            # Process each component
            for structure in salary_structures:
                component = structure.component
                amount = structure.amount or Decimal('0.00')

                # Save to PayslipComponent
                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=component,
                    amount=amount
                )

                # Categorize amounts
                if component.component_type == 'addition':
                    total_additions += amount
                    if component.name.lower() == 'basic':
                        basic_salary = amount
                elif component.component_type == 'deduction':
                    total_deductions += amount

            # Calculate gross and net salary
            gross_salary = total_additions
            net_salary = gross_salary - total_deductions

            # Update payslip
            payslip.basic_salary = basic_salary
            payslip.gross_salary = gross_salary
            payslip.net_salary = net_salary
            payslip.total_additions = total_additions
            payslip.total_deductions = total_deductions
            payslip.status = 'processed'  # Mark as processed since no formula errors
            payslip.save()

        # Mark payroll as processed
        payroll_run.status = 'processed'
        payroll_run.save()


def eval_formula(formula, components_dict):
    """Evaluate the payroll formula, defaulting missing components to 0."""
    import re
    # Extract variables from the formula
    variables = set(re.findall(r'[a-zA-Z_]+', formula))

    # Check for missing components
    missing_vars = [var for var in variables if
                    var not in components_dict and var not in ['+', '-', '*', '/', '(', ')']]
    if missing_vars:
        logger.warning(f"Missing components in formula: {missing_vars}. Defaulting to 0.")
        for var in missing_vars:
            components_dict[var] = Decimal('0.00')

    # Replace component names with their values
    for name, value in components_dict.items():
        formula = formula.replace(name, str(value))

    try:
        return Decimal(str(eval(formula)))
    except Exception as e:
        raise ValueError(f"Error evaluating formula '{formula}': {e}")


# PayrollManagement/utils.py or PayrollManagement/pdf_utils.py
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from .models import Payslip, PayslipComponent
import io


def generate_payslip_pdf(request, payslip):
    """Generate a PDF payslip for the given Payslip instance."""
    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Create the PDF object using ReportLab
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Styles for text
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']

    # Fetch the company name from the tenant
    company_name = request.tenant.name if hasattr(request, 'tenant') else "Default Company Name"

    # Add company header
    elements.append(Paragraph(f"Company Name: {company_name}", title_style))
    elements.append(Paragraph(f"Payslip for {payslip.employee.emp_first_name} {payslip.employee.emp_last_name or ''}",
                              normal_style))

    # Updated payroll period display to use start_date and end_date
    payroll_period = f"{payslip.payroll_run.start_date.strftime('%d %b %Y')} to {payslip.payroll_run.end_date.strftime('%d %b %Y')}"
    elements.append(Paragraph(f"Payroll Period: {payroll_period}", normal_style))

    # Add working days information
    elements.append(Paragraph(f"Working Days: {payslip.days_worked}/{payslip.total_working_days}", normal_style))
    elements.append(Spacer(1, 12))

    # Employee details (unchanged)
    employee_details = [
        ["Employee Code", payslip.employee.emp_code],
        ["First Name", payslip.employee.emp_first_name],
        ["Last Name", payslip.employee.emp_last_name or "N/A"],
        ["Department", payslip.employee.emp_dept_id.dept_name if payslip.employee.emp_dept_id else "N/A"],
        ["Branch", payslip.employee.emp_branch_id.branch_name if payslip.employee.emp_branch_id else "N/A"],
        ["Designation", payslip.employee.emp_desgntn_id.desgntn_name if payslip.employee.emp_desgntn_id else "N/A"],
        ["Joining Date", payslip.employee.emp_joined_date.strftime("%Y-%m-%d")],
    ]
    employee_table = Table(employee_details, colWidths=[200, 200])
    employee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 12))

    # Salary components table with new fields
    components = PayslipComponent.objects.filter(payslip=payslip)
    data = [["Component", "Type", "Amount"]]
    for component in components:
        data.append(
            [component.component.name, component.component.get_component_type_display(), f"{component.amount:.2f}"])

    # Add totals including new fields
    data.append(["", "", ""])
    data.append(["Gross Salary", "", f"{payslip.gross_salary:.2f}"])
    data.append(["Total Additions", "", f"{payslip.total_additions:.2f}"])
    data.append(["Total Deductions", "", f"{payslip.total_deductions:.2f}"])
    # data.append(["Pro-rata Adjustment", "", f"{payslip.pro_rata_adjustment:.2f}"])
    # data.append(["Arrears", "", f"{payslip.arrears:.2f}"])
    data.append(["Net Salary", "", f"{payslip.net_salary:.2f}"])

    salary_table = Table(data, colWidths=[200, 100, 200])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Right-align amounts
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 12))

    # Footer
    elements.append(Paragraph("Generated by ZEO HRMS", normal_style))

    # Build the PDF
    pdf.build(elements)

    # Get the PDF data from the buffer
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    # Return the PDF as an HTTP response
    filename = f"payslip_{payslip.employee.emp_code}_{payslip.payroll_run.start_date.strftime('%Y%m')}.pdf"
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response