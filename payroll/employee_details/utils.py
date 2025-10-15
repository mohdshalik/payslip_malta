import os
from django.conf import settings
from pdfrw import PdfReader, PdfWriter, PdfName
from decimal import Decimal
from simpleeval import simple_eval

def generate_fs5_for_employee(employee, payroll_run, payslip, output_dir=None):
    from .models import PayslipComponent, SalaryComponent, EmployeeSalaryStructure

    if not output_dir:
        output_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', 'media'), "fs5")
    os.makedirs(output_dir, exist_ok=True)

    template_path = os.path.join(getattr(settings, 'BASE_DIR', ''), "static/forms/fs5-fillable.pdf")
    output_pdf_path = os.path.join(
        output_dir, f"FS5_{employee.emp_code}_{payroll_run.month}_{payroll_run.year}.pdf"
    )

    company = employee.company

    # ✅ Field Mapping
    FS5_FIELD_MAP = {
        "C1a": "untitled10",   # Overtime (eligible for 15% tax)
        "C2": "untitled11",    # Gross Emoluments
        "C3": "untitled12",    # Fringe Benefits
        "D1": "untitled14",    # Tax Deductions (Main)
        "D2": "untitled15",    # Tax Deductions (Part-time)
        "D3": "untitled16",    # Tax Arrears
        "D5": "untitled18",    # Social Security
        "D5a": "untitled19",   # Maternity Fund
    }

    # ✅ Initialize FS5 base fields
    field_values = {
        "untitled1": company.name or "",
        "untitled2": company.address or "",
        "untitled3": getattr(company, "post_code", "") or "",
        "untitled4": company.phone_number or "",
        "untitled5": "",
        "untitled6": getattr(company, "pe_number", company.tax_id) or "",
        "untitled7": f"{payroll_run.get_month_display()} {payroll_run.year}",
        "untitled8": 1,  # Main/Other
        "untitled9": 1,  # Part-time
        **{f"untitled{i}": 0.0 for i in range(10, 22)},
    }

    print(f"\n📄 Generating FS5 for Employee: {employee.emp_code} ({employee.first_name})")

    # ✅ 1️⃣ Start with payslip components (selected ones)
    payslip_components = PayslipComponent.objects.filter(payslip=payslip).select_related("component")
    for comp in payslip_components:
        fs5_field = comp.component.fs5_field
        if fs5_field and fs5_field in FS5_FIELD_MAP:
            pdf_field = FS5_FIELD_MAP[fs5_field]
            field_values[pdf_field] += float(comp.amount)
            print(f"  ➕ From Payslip: {comp.component.name} ({fs5_field}) = {comp.amount}")

    # ✅ 2️⃣ Include all remaining FS5-linked components (even if not selected in payroll)
    all_fs5_components = SalaryComponent.objects.exclude(fs5_field__isnull=True).exclude(fs5_field="Not Applicable")
    emp_structures = {s.component.id: s.amount for s in EmployeeSalaryStructure.objects.filter(employee=employee)}

    # Create context for formula evaluation
    context = {}
    for comp in payslip_components:
        context[comp.component.code] = float(comp.amount)

    for comp in all_fs5_components:
        # Skip if already included via payslip
        if any(pc.component_id == comp.id for pc in payslip_components):
            continue

        # If the employee has an amount for this component
        base_amount = float(emp_structures.get(comp.id, 0))
        value = 0.0

        if comp.formula:
            try:
                value = simple_eval(comp.formula, names=context)
            except Exception as e:
                print(f" ⚠️ Formula error for {comp.name}: {e}")
        elif base_amount:
            value = base_amount

        if value and comp.fs5_field in FS5_FIELD_MAP:
            pdf_field = FS5_FIELD_MAP[comp.fs5_field]
            field_values[pdf_field] += float(value)
            print(f"  ➕ Auto Added: {comp.name} ({comp.fs5_field}) = {value}")

    # ✅ Totals
    field_values["untitled13"] = field_values["untitled10"] + field_values["untitled11"] + field_values["untitled12"]
    field_values["untitled17"] = field_values["untitled14"] + field_values["untitled15"] + field_values["untitled16"]
    field_values["untitled20"] = field_values["untitled17"] + field_values["untitled18"] + field_values["untitled19"]
    field_values["untitled21"] = field_values["untitled20"]

    print("\n✅ Final FS5 Field Values:")
    for key in sorted(field_values.keys(), key=lambda x: int(x.replace("untitled", "")) if x.startswith("untitled") else 100):
        print(f"  {key}: {field_values[key]}")

    # ✅ Fill PDF
    pdf = PdfReader(template_path)
    for page in pdf.pages:
        annotations = page.get("/Annots")
        if annotations:
            for annot in annotations:
                key = annot.get("/T")
                if key:
                    key_str = key.to_unicode() if hasattr(key, 'to_unicode') else str(key).strip("()")
                    if key_str in field_values:
                        value = field_values[key_str]
                        formatted_value = str(round(value, 2)) if isinstance(value, (int, float)) else value
                        annot.update({
                            PdfName("V"): formatted_value,
                            PdfName("Ff"): 1
                        })
                        annot.update({PdfName("AP"): None})

    PdfWriter(output_pdf_path, trailer=pdf).write()
    print(f"\n📁 FS5 generated: {output_pdf_path}")
    return output_pdf_path



def debug_pdf_fields(template_path):
    from pdfrw import PdfReader
    pdf = PdfReader(template_path)
    print("\n🔍 LIST OF FORM FIELD NAMES IN YOUR FS5 TEMPLATE:\n")
    for page in pdf.pages:
        annotations = page.get("/Annots")
        if annotations:
            for annot in annotations:
                key = annot.get("/T")
                if key:
                    key_str = key.to_unicode() if hasattr(key, 'to_unicode') else str(key).strip("()")
                    print(key_str)
