from django.db import models

# Create your models here.
class Role(models.Model):
    role_name=models.CharField(max_length=50,unique=True)
    

class Employee(models.Model):
    company = models.ForeignKey('company_details.Company', on_delete=models.CASCADE, related_name='employees')
    emp_code = models.CharField(max_length=50,unique=True)
    first_name = models.CharField(max_length=50,null=True)
    last_name = models.CharField(max_length=50,null=True)
    address = models.CharField(max_length=100,null=True )
    email = models.EmailField(unique=True,null=True)
    job_title=models.ForeignKey('role',on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    hire_date = models.DateField()
    social_security_no = models.CharField(max_length=50,unique=True,null=True)
    Tax_Registration_Number = models.CharField(max_length=50,unique=True,null=True)
    Bank_Account_Number = models.CharField(max_length=50,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fss_status = models.CharField(max_length=10, null=True, blank=True)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class SalaryComponent(models.Model):
    COMPONENT_TYPES = [
        ('deduction', 'Deduction'),
        ('addition', 'Addition'),
        ('others', 'Others'),
    ]

    name = models.CharField(max_length=100, unique=True)  # Component name (e.g., HRA, PF)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    code = models.CharField(max_length=20, null=True)
    deduct_leave = models.BooleanField(default=False)
    is_fixed = models.BooleanField(default=True, help_text="Is this component fixed (True) or variable (False)?")
    formula = models.CharField(max_length=255, blank=True, null=True,
                               help_text="Formula to calculate this component (e.g., 'basic_salary * 0.4')")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"


class EmployeeSalaryStructure(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='salary_structures')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='employee_components')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                 help_text="Amount for this component")
    is_active = models.BooleanField(default=True, help_text="Is this component active for the employee?")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'component')  # Ensure no duplicate components for an employee

    def __str__(self):
        return f"{self.employee} - {self.component.name} ({self.amount})"


class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),  # Added status
    ]

    name = models.CharField(max_length=100, blank=True, help_text="Optional payroll run name")  # New field
    start_date = models.DateField(help_text="Start date of payroll period")
    end_date = models.DateField(help_text="End date of payroll period")
    payment_date = models.DateField(null=True, blank=True, help_text="When employees will be paid")  # New field

    branch = models.ForeignKey('company_details.Company', on_delete=models.SET_NULL, null=True, blank=True)
    # department = models.ForeignKey('OrganisationManager.dept_master', on_delete=models.SET_NULL, null=True, blank=True)
    # category = models.ForeignKey('OrganisationManager.ctgry_master', on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_employees(self):
        # from EmpManagement.models import emp_master
        employees = Employee.objects.all()
        # if self.branch:
        #     employees = employees.filter(emp_branch_id=self.branch)
        # if self.department:
        #     employees = employees.filter(emp_dept_id=self.department)
        # if self.category:
        #     employees = employees.filter(emp_ctgry_id=self.category)
        return employees

    def __str__(self):
        return f"Payroll - {self.get_month_display()} {self.year} ({self.status})"


class Payslip(models.Model):
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='payslips')
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_additions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for working days
    total_working_days = models.PositiveIntegerField(default=0, help_text="Total working days in the payroll period")
    days_worked = models.PositiveIntegerField(default=0, help_text="Number of days the employee worked")
    pro_rata_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                              help_text="Pro-rata adjustment")  # New field
    arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                  help_text="Arrears amount")  # New field

class PayslipComponent(models.Model):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.payslip.employee} - {self.component.name} ({self.amount})"
