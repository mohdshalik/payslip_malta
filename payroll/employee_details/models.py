from django.db import models
from datetime import datetime, timedelta,timezone, time,date
from django.contrib.auth.models import User
from calendar import monthrange 
import decimal
from decimal import Decimal

# Create your models here.
class category(models.Model):
    name = models.CharField(max_length=50,unique=True)


class Employee(models.Model):
    Employee_type=[
        ('part_time','Part Time'),
        ('full_time','Full Time')
    ]
    company = models.ForeignKey('company_details.Company', on_delete=models.CASCADE, related_name='company')
    # emp_dept_id = models.ForeignKey('company_details.Department', on_delete=models.CASCADE, related_name='dept')
    category=models.ForeignKey('category', on_delete=models.CASCADE, related_name='category')
    

    emp_code = models.CharField(max_length=50,unique=True)
    first_name = models.CharField(max_length=50,null=True)
    last_name = models.CharField(max_length=50,null=True)
    address = models.CharField(max_length=100,null=True )
    email = models.EmailField(unique=True,null=True)
    type_of_employment=models.CharField(max_length=20,choices=Employee_type)
    job_title=models.ForeignKey('company_details.Role',on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    hired_date = models.DateField()
    social_security_no = models.CharField(max_length=50,unique=True,null=True)
    Tax_Registration_Number = models.CharField(max_length=50,unique=True,null=True)
    Bank_Account_Number = models.CharField(max_length=50,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fss_status = models.CharField(max_length=10, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class SalaryComponent(models.Model):
    COMPONENT_TYPES = [
        ('deduction', 'Deduction'),
        ('addition', 'Addition'),
        ('others', 'Others'),
    ]

    FS5_CATEGORIES = [
        (None, 'Not Applicable'),
        ('C1a', 'Overtime'),
        ('C3', 'Fringe Benefits'),
        ('D1', 'Tax Deductions (Main)'),
        ('D2', 'Tax Deductions (Overtime)'),
        ('D3', 'Tax Deductions (Part-time)'),
        ('D4', 'Tax Arrears'),
        ('D6', 'Social Security Contributions'),
        ('D7', 'Maternity Fund'),
    ]

    name = models.CharField(max_length=100, unique=True)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    code = models.CharField(max_length=20, null=True)
    is_fixed = models.BooleanField(default=True)
    for_formula = models.BooleanField(default=True)
    formula = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # New FS5 mapping field
    fs5_related =models.BooleanField(default=False)
    fs5_category = models.CharField(
        max_length=10, choices=FS5_CATEGORIES,
        null=True, blank=True,
        help_text="If this component contributes to FS5, select the appropriate field."
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

    def get_employees(self):
    # Return all employees, no department restriction
        return Employee.objects.all()

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and self.status == 'pending':
            self.generate_payslips()

    def generate_payslips(self):
        total_days = monthrange(self.year, self.month)[1]
        month_start = date(self.year, self.month, 1)
        month_end = date(self.year, self.month, total_days)

        employees = self.get_employees()

        for employee in employees:
            # Skip if joined after payroll month
            if employee.hired_date > month_end:
                continue

            # Effective start date for this employee
            from_date = max(employee.hired_date, month_start)
            days_worked = (month_end - from_date).days + 1

            # Prevent duplicate payslips
            if Payslip.objects.filter(payroll_run=self, employee=employee).exists():
                continue

            salary_components = EmployeeSalaryStructure.objects.filter(
                employee=employee, 
                is_active=True
            )

            total_deductions = decimal.Decimal('0.00')
            total_additions = decimal.Decimal('0.00')
            gross_salary = decimal.Decimal('0.00')

            # Create payslip
            payslip = Payslip.objects.create(
                payroll_run=self,
                employee=employee,
                total_working_days=total_days,
                from_date=month_start,
                to_date=month_end,
                days_worked=days_worked,
                status='pending'
            )

            # Process salary components
            for salary_component in salary_components:
                amount = salary_component.amount or decimal.Decimal('0.00')

                if not salary_component.component.is_fixed:
                    # prorate based on days worked
                    amount = (amount * days_worked) / total_days

                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=salary_component.component,
                    amount=amount
                )

                if salary_component.component.component_type == 'addition':
                    total_additions += amount
                    gross_salary += amount
                elif salary_component.component.component_type == 'deduction':
                    total_deductions += amount

            # Update payslip totals
            payslip.gross_salary = gross_salary
            payslip.total_additions = total_additions
            payslip.total_deductions = total_deductions
            payslip.net_salary = gross_salary - total_deductions
            payslip.save()

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
    
    
class FS5Report(models.Model):
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(null=True, blank=True)  # optional if you want monthly FS5
    created_at = models.DateTimeField(auto_now_add=True)

    # Payer info (from Company/Employer model normally)
    business_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    payer_vat_no = models.CharField(max_length=50, blank=True, null=True)

    # Totals (aggregated from Payslip + PayslipComponent)
    number_of_payees_main = models.PositiveIntegerField(default=0)  # B1
    number_of_payees_parttime = models.PositiveIntegerField(default=0)  # B2

    gross_emoluments_main = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # C1
    overtime = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # C1a
    gross_emoluments_parttime = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # C2
    fringe_benefits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # C3
    total_gross_emoluments = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # C4

    tax_deductions_main = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D1
    tax_deductions_overtime = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D2
    tax_deductions_parttime = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D3
    tax_deductions_arrears = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D4
    total_tax_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D5

    ssc_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D6
    maternity_fund = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D7
    total_due_commissioner = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # D8

    def __str__(self):
        return f"FS5 - {self.month or ''}/{self.year}"

