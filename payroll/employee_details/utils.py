import os
from django.conf import settings
from pdfrw import PdfReader, PdfWriter, PdfName
from decimal import Decimal
from simpleeval import simple_eval

def generate_fs5_for_employee(employee, payroll_run, payslip, output_dir=None):
    import os
    from .models import PayslipComponent, SalaryComponent, EmployeeSalaryStructure
    # from pypdf import PdfReader, PdfWriter, PdfName
    # from simpleeval import simple_eval
    from django.conf import settings

    if not output_dir:
        output_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', 'media'), "fs5")
    os.makedirs(output_dir, exist_ok=True)

    template_path = os.path.join(getattr(settings, 'BASE_DIR', ''), "static/forms/fs5-fillable.pdf")
    output_pdf_path = os.path.join(
        output_dir, f"FS5_{employee.emp_code}_{payroll_run.month}_{payroll_run.year}.pdf"
    )

    company = employee.company

    # ✅ FS5 field mapping
    FS5_FIELD_MAP = {
        "C1": "untitled10",
        "C1a": "untitled11",
        "C2": "untitled12",
        "C3": "untitled13",
        "C4": "untitled14",
        "D1": "untitled15",
        "D1a": "untitled16",
        "D2": "untitled17",
        "D3": "untitled18",
        "D4": "untitled19",
        "D5": "untitled20",
        "D5a": "untitled22",
        "D6": "untitled24"
    }

    # ✅ Initialize all fields
    field_values = {v: 0.0 for v in FS5_FIELD_MAP.values()}

    # Base company info
    field_values.update({
        "untitled1": company.name or "",
        "untitled2": company.address or "",
        "untitled3": getattr(company, "post_code", "") or "",
        "untitled4": company.phone_number or "",
        "untitled5": "",
        "untitled6": getattr(company, "pe_number", company.tax_id) or "",
        "untitled7": f"{payroll_run.get_month_display()} {payroll_run.year}",
        "untitled8": 1,  # Main/Other
        "untitled9": 1,  # Part-time
    })

    print(f"\n📄 Generating FS5 for Employee: {employee.emp_code} ({employee.first_name})")

    # ✅ 1️⃣ Payslip components
    payslip_components = PayslipComponent.objects.filter(payslip=payslip).select_related("component")
    for comp in payslip_components:
        fs5_field = comp.component.fs5_field
        if fs5_field and fs5_field in FS5_FIELD_MAP:
            pdf_field = FS5_FIELD_MAP[fs5_field]
            field_values[pdf_field] += float(comp.amount)
            print(f"  ➕ Payslip: {comp.component.name} ({fs5_field}) = {comp.amount}")

    # ✅ 2️⃣ All remaining FS5-linked components
    all_fs5_components = SalaryComponent.objects.exclude(fs5_field__isnull=True).exclude(fs5_field="Not Applicable")
    emp_structures = {s.component.id: s.amount for s in EmployeeSalaryStructure.objects.filter(employee=employee)}

    # Context for formula evaluation
    context = {comp.component.code: float(comp.amount) for comp in payslip_components}

    for comp in all_fs5_components:
        if any(pc.component_id == comp.id for pc in payslip_components):
            continue

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

        # Update context for dependent formulas
        context[comp.code] = value

    # ✅ 3️⃣ Calculate totals
    field_values[FS5_FIELD_MAP["C4"]] = (
        field_values[FS5_FIELD_MAP["C1"]] +
        field_values[FS5_FIELD_MAP["C1a"]] +
        field_values[FS5_FIELD_MAP["C2"]] +
        field_values[FS5_FIELD_MAP["C3"]]
    )

    field_values[FS5_FIELD_MAP["D4"]] = (
        field_values[FS5_FIELD_MAP["D1"]] +
        field_values[FS5_FIELD_MAP["D1a"]] +
        field_values[FS5_FIELD_MAP["D2"]] +
        field_values[FS5_FIELD_MAP["D3"]]
    )

    field_values[FS5_FIELD_MAP["D6"]] = (
        field_values[FS5_FIELD_MAP["D5"]] +
        field_values[FS5_FIELD_MAP["D5a"]]
    )

    print("\n✅ Final FS5 Field Values:")
    for key, value in field_values.items():
        print(f"  {key}: {value}")

    # ✅ 4️⃣ Fill PDF
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
