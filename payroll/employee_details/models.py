from django.db import models
from datetime import datetime, timedelta,timezone, time,date
from django.contrib.auth.models import User
from calendar import monthrange 
import decimal

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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_structures')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='employee_components')
    amount = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
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
        # Get total working days in the month
        total_days = monthrange(self.year, self.month)[1]
        from_date = date(self.year, self.month, 1)
        to_date = date(self.year, self.month, total_days)
        
        # Get all employees based on department filter
        employees = self.get_employees()
        
        for employee in employees:
            # Check if payslip already exists for this employee and payroll run
            if not Payslip.objects.filter(payroll_run=self, employee=employee).exists():
                # Get employee salary structure
                salary_components = EmployeeSalaryStructure.objects.filter(
                    employee=employee, 
                    is_active=True
                )
                
                # Calculate totals
                gross_salary = decimal.Decimal('0.00')
                total_deductions = decimal.Decimal('0.00')
                total_additions = decimal.Decimal('0.00')
                
                # Create payslip
                payslip = Payslip.objects.create(
                    payroll_run=self,
                    employee=employee,
                    total_working_days=total_days,
                    from_date=from_date,
                    to_date=to_date,
                    # days_worked=total_days,  # Assuming full attendance, modify as needed
                    status='pending'
                )
                
                # Process each salary component
                for salary_component in salary_components:
                    amount = salary_component.amount or decimal.Decimal('0.00')
                    
                    # # Apply pro-rata adjustment if needed
                    # if not salary_component.component.is_fixed:
                    #     amount = (amount * payslip.days_worked) / payslip.total_working_days
                        
                    # Create payslip component
                    PayslipComponent.objects.create(
                        payslip=payslip,
                        component=salary_component.component,
                        amount=amount
                    )
                    
                    # Update totals based on component type
                    if salary_component.component.component_type == 'addition':
                        total_additions += amount
                        gross_salary += amount
                    elif salary_component.component.component_type == 'deduction':
                        total_deductions += amount
                
                # Update payslip with calculated totals
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
    gross_salary = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)  # Added
    net_salary = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    total_additions = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for working days
    total_working_days = models.PositiveIntegerField(default=0, help_text="Total working days in the payroll period")
    from_date = models.DateField(null=True, blank=True, help_text="Start date of payroll period")
    to_date = models.DateField(null=True, blank=True, help_text="End date of payroll period")
    # days_worked = models.PositiveIntegerField(default=0, help_text="Number of days the employee worked")
    # pro_rata_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
    #              
    
class PayslipComponent(models.Model):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=4)

    def __str__(self):
        return f"{self.payslip.employee} - {self.component.name} ({self.amount})"
    


