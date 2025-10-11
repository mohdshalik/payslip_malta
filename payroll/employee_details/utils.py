import os
from django.conf import settings
from pdfrw import PdfReader, PdfWriter, PdfName


def generate_fs5_for_employee(employee, payroll_run, payslip, output_dir=None):
    from .models import PayslipComponent 

    if not output_dir:
        # Assuming settings.MEDIA_ROOT is defined
        output_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', 'media'), "fs5")
    os.makedirs(output_dir, exist_ok=True)

    template_path = os.path.join(getattr(settings, 'BASE_DIR', ''), "static/forms/fs5-fillable.pdf")
    output_pdf_path = os.path.join(
        output_dir, f"FS5_{employee.emp_code}_{payroll_run.month}_{payroll_run.year}.pdf"
    )

    company = employee.company
    payslip_components = PayslipComponent.objects.filter(payslip=payslip).select_related("component")

    # ✅ CORRECTED FS5 FIELD MAP based on sequential 'untitled' field names.
    # C Section (untitled10 - untitled13)
    # D Section (untitled15 - untitled18, untitled20 - untitled21)
    FS5_FIELD_MAP = {
    "C1a": "untitled10",   # Overtime (eligible for 15% tax)
    "C2": "untitled11",    # Gross Emoluments
    "C3": "untitled12",    # Fringe Benefits
    "D1": "untitled14",    # Tax Deductions (Main/Other)
    "D2": "untitled15",    # Tax Deductions (Part-time)
    "D3": "untitled16",    # Tax Arrears
    "D5": "untitled18",    # Social Security
    "D5a": "untitled19",   # Maternity Fund
}


    # ✅ Initialize base fields (A, B sections)
    field_values = {
    # Section A: Company info
    "untitled1": company.name or "",
    "untitled2": company.address or "",
    "untitled3": getattr(company, "post_code", "") or "",
    "untitled4": company.phone_number or "",
    "untitled5": "",
    "untitled6": getattr(company, "pe_number", company.tax_id) or "",
    "untitled7": f"{payroll_run.get_month_display()} {payroll_run.year}",

    # Section B: Number of payees
    "untitled8": 1,  # Main/Other
    "untitled9": 1,  # Part-time

    # Initialize all numeric fields (10–21) to 0
    **{f"untitled{i}": 0.0 for i in range(10, 22)},
}

    print(f"\n📄 Generating FS5 for Employee: {employee.emp_code} ({employee.first_name})")

    # ✅ Aggregate salary component values based on the corrected map
    for comp in payslip_components:
        fs5_field = comp.component.fs5_field
        if fs5_field and fs5_field in FS5_FIELD_MAP:
            pdf_field = FS5_FIELD_MAP[fs5_field]
            # Ensure value is treated as a float
            try:
                field_values[pdf_field] += float(comp.amount)
            except (ValueError, TypeError):
                print(f" ⚠️ Could not convert amount for {comp.component.name}. Skipping aggregation.")
            print(f"  ➕ Added {comp.component.name} ({fs5_field}) to {pdf_field} = {comp.amount}")

    # ✅ CORRECTED Computation of totals
    # C4 (Total Gross) = C1 + C1A + C2 + C3
    field_values["untitled14"] = (
        field_values["untitled10"] + field_values["untitled11"] + 
        field_values["untitled12"] + field_values["untitled13"]
    )

    # D4 (Total Tax Deductions) = D1 + D1A + D2 + D3
    field_values["untitled19"] = (
        field_values["untitled15"] + field_values["untitled16"] + 
        field_values["untitled17"] + field_values["untitled18"]
    )

    # D6 (Total Due to Commissioner) = D4 + D5 + D5a
    field_values["untitled22"] = (
        field_values["untitled19"] + field_values["untitled20"] + field_values["untitled21"]
    )
    
    # E1 (Total Payment) = D6
    field_values["untitled23"] = field_values["untitled22"] # E1 = D6

    print("\n✅ Final FS5 Field Values:")
    for key in sorted(field_values.keys(), key=lambda x: int(x.replace("untitled", "")) if x.startswith("untitled") else 100):
        print(f"  {key}: {field_values[key]}")

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
                        # Format floats to 2 decimal places (Euro cents)
                        formatted_value = str(round(value, 2)) if isinstance(value, (int, float)) else value
                        annot.update({
                            PdfName("V"): formatted_value,
                            PdfName("Ff"): 1 # Set the 'read-only' flag after filling, which often helps display
                        })
                        annot.update({PdfName("AP"): None}) # Clear appearance stream for better display

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
