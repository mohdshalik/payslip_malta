from django.db import models
from datetime import datetime, timedelta,timezone, time,date
from django.contrib.auth.models import User
from calendar import monthrange 
import decimal
from decimal import Decimal
from simpleeval import simple_eval  
import os
from .utils import generate_fs5_for_employee

# Create your models here.
class category(models.Model):
    name = models.CharField(max_length=50,unique=True)


class Employee(models.Model):
    Employee_type = [
        ('part_time', 'Part Time'),
        ('full_time', 'Full Time')
    ]

    company = models.ForeignKey(
        'company_details.Company',
        on_delete=models.CASCADE,
        related_name='company',
        null=True, blank=True
    )
    category = models.ForeignKey(
        'category',
        on_delete=models.CASCADE,
        related_name='category',
        null=True, blank=True
    )

    emp_code = models.CharField(max_length=50, unique=True)  # REQUIRED
    first_name = models.CharField(max_length=50)  # REQUIRED
    address = models.CharField(max_length=100)  # REQUIRED

    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    type_of_employment = models.CharField(
        max_length=20,
        choices=Employee_type,
        null=True, blank=True
    )
    job_title = models.ForeignKey(
        'company_details.Role',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    hired_date = models.DateField(null=True, blank=True)
    social_security_no = models.CharField(max_length=50, unique=True, null=True, blank=True)
    Tax_Registration_Number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    Bank_Account_Number = models.CharField(max_length=50, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fss_status = models.CharField(max_length=10, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}"
    

class SalaryComponent(models.Model):
    COMPONENT_TYPES = [
        ('deduction', 'Deduction'),
        ('addition', 'Addition'),
        ('others', 'Others'),
    ]

    # ✅ CORRECTED FS5 CATEGORIES: Now mapping to the distinct fields in Section C and D of FS5.
    FS5_CATEGORIES = [
    (None, 'Not Applicable'),
    ('C1a', 'Overtime (eligible for 15% tax deduction)'),
    ('C2', 'Gross Emoluments (FSS Main/Other)'),
    ('C3', 'Taxable Fringe Benefits'),
    ('D1', 'Tax Deductions (FSS Main/Other)'),
    ('D2', 'Tax Deductions (FSS Part-time)'),
    ('D3', 'Tax Arrears'),
    ('D5', 'Social Security Contributions'),
    ('D5a', 'Maternity Fund Contributions'),
]
    name = models.CharField(max_length=100, unique=True)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    code = models.CharField(max_length=20, null=True)
    is_fixed = models.BooleanField(default=True)
    for_formula = models.BooleanField(default=True)
    formula = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    fs5_field = models.CharField(
        max_length=10,
        choices=FS5_CATEGORIES,
        null=True, blank=True,
        help_text="Where this component should appear on FS5 form"
    )

    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"



class EmployeeSalaryStructure(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_structures')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='employee_components')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                 help_text="Amount for this component")
    is_active = models.BooleanField(default=True, help_text="Is this component active for the employee?")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'component')  # Ensure no duplicate components for an employee
        ordering = ['date_created']

    def __str__(self):
        return f"{self.employee} - {self.component.name} ({self.amount})"


class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]
    
    MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]
    
    name = models.CharField(max_length=100, blank=True, help_text="Optional payroll run name")
    month = models.IntegerField(choices=MONTH_CHOICES, help_text="Month of the payroll period")
    year = models.IntegerField(help_text="Year of the payroll period")
    payment_date = models.DateField(null=True, blank=True, help_text="When employees will be paid")
    # branch = models.ForeignKey('OrganisationManager.brnch_mstr', on_delete=models.SET_NULL, null=True, blank=True)
    # department = models.ForeignKey('company_details.Department', on_delete=models.SET_NULL, null=True, blank=True)
    # category = models.ForeignKey('OrganisationManager.ctgry_master', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    components = models.ManyToManyField('SalaryComponent', blank=True, help_text="Components to include in this payroll run")
    
    def get_employees(self):
    # Return all employees, no department restriction
        return Employee.objects.all()

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        # if is_new and self.status == 'pending':
        #     self.generate_payslips()

    import decimal
    from calendar import monthrange
    from datetime import date

    # Assuming your models (Payslip, PayslipComponent, SalaryComponent, EmployeeSalaryStructure) 
    # and the simple_eval function are accessible in this scope.

    def generate_payslips(self):
        total_days = monthrange(self.year, self.month)[1]
        month_start = date(self.year, self.month, 1)
        month_end = date(self.year, self.month, total_days)

        employees = self.get_employees()
        print(f"\n===== PayrollRun {self.id} - Generating payslips =====")
        print(f"Payroll month/year: {self.month}/{self.year}")
        print(f"Total working days in month: {total_days}")

        selected_components = self.components.all()
        print("Selected components for payroll run:")
        for c in selected_components:
            print(f"  - {c.id}: {c.name} (for_formula={c.for_formula})")

        if not selected_components.exists():
            print(f"⚠️ No components selected for PayrollRun {self.id}")
            return

        non_formula_components = selected_components.filter(for_formula=False)
        formula_components = selected_components.filter(for_formula=True)
        non_formula_ids = list(non_formula_components.values_list('id', flat=True))

        for employee in employees:
            if employee.hired_date and employee.hired_date > month_end:
                print(f"Skipping {employee.emp_code}: hired after payroll month")
                continue

            from_date = max(employee.hired_date or month_start, month_start)
            days_worked = (month_end - from_date).days + 1

            if Payslip.objects.filter(payroll_run=self, employee=employee).exists():
                print(f"Skipping {employee.emp_code}: payslip already exists")
                continue

            print(f"\n--- Generating payslip for employee {employee.emp_code} ---")
            print(f"Hired date: {employee.hired_date}, Days worked: {days_worked}")

            salary_structures = EmployeeSalaryStructure.objects.filter(
                employee=employee,
                component_id__in=non_formula_ids,
                is_active=True
            ).select_related("component")

            total_deductions = Decimal('0.00')
            total_additions = Decimal('0.00')
            gross_salary = Decimal('0.00')

            payslip = Payslip.objects.create(
                payroll_run=self,
                employee=employee,
                total_working_days=total_days,
                from_date=month_start,
                to_date=month_end,
                days_worked=days_worked,
                status='pending'
            )

            context = {}

            # -------------------
            # Pass 1: Non-formula components
            # -------------------
            for structure in salary_structures:
                comp = structure.component
                amount = Decimal(structure.amount or 0)
                if not comp.is_fixed:
                    amount = (amount * days_worked) / total_days

                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=comp,
                    amount=amount.quantize(Decimal('0.01'))
                )

                if comp.component_type == 'addition':
                    total_additions += amount
                    gross_salary += amount
                elif comp.component_type == 'deduction':
                    total_deductions += amount

                if comp.code:
                    context[comp.code] = float(amount)

                print(f"Non-formula component added: {comp.name} = {amount}")

            context['gross_salary'] = float(gross_salary)

            # -------------------
            # Pass 2: Formula components
            # -------------------
            for comp in formula_components:
                if not comp.formula:
                    continue
                try:
                    formula = comp.formula.strip()
                    print(f"\nEvaluating formula component: {comp.name} ({comp.code})")
                    print(f"Formula: {formula}")
                    print(f"Context before formula: {context}")

                    value = simple_eval(formula, names=context)
                    amount = Decimal(str(value))
                    print(f"Formula result: {amount}")
                except Exception as e:
                    print(f"❌ Error evaluating formula {comp.formula} for {employee.emp_code}: {e}")
                    amount = Decimal('0.00')

                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=comp,
                    amount=amount.quantize(Decimal('0.01'))
                )

                if comp.component_type == 'addition':
                    total_additions += amount
                    gross_salary += amount
                elif comp.component_type == 'deduction':
                    total_deductions += amount

                if comp.code:
                    context[comp.code] = float(amount)

            # -------------------
            # Final totals
            # -------------------
            payslip.gross_salary = gross_salary.quantize(Decimal('0.01'))
            payslip.total_additions = total_additions.quantize(Decimal('0.01'))
            payslip.total_deductions = total_deductions.quantize(Decimal('0.01'))
            payslip.net_salary = (gross_salary - total_deductions).quantize(Decimal('0.01'))
            payslip.save()
            generate_fs5_for_employee(employee, self, payslip)




    def __str__(self):  
        return f"Payroll - {self.get_month_display()} {self.year} ({self.status})"


class Payslip(models.Model):
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_additions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for working days
    total_working_days = models.PositiveIntegerField(default=0, help_text="Total working days in the payroll period")
    from_date = models.DateField(null=True, blank=True, help_text="Start date of payroll period")
    to_date = models.DateField(null=True, blank=True, help_text="End date of payroll period")
    days_worked = models.IntegerField(default=0)
    # days_worked = models.PositiveIntegerField(default=0, help_text="Number of days the employee worked")
    # pro_rata_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
    #              
    
 
class PayslipComponent(models.Model):
   payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='components')
   component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
   amount = models.DecimalField(max_digits=10, decimal_places=2)
   def __str__(self):
       return f"{self.payslip.employee} - {self.component.name} ({self.amount})" 

