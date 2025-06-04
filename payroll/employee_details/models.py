from django.db import models
from datetime import datetime, timedelta,timezone, time,date


# Create your models here.


class Employee(models.Model):
    company = models.ForeignKey('company_details.Company', on_delete=models.CASCADE, related_name='employees')
    emp_dept_id = models.ForeignKey('company_details.Department', on_delete=models.CASCADE, related_name='employees')
    

    emp_code = models.CharField(max_length=50,unique=True)
    first_name = models.CharField(max_length=50,null=True)
    last_name = models.CharField(max_length=50,null=True)
    address = models.CharField(max_length=100,null=True )
    email = models.EmailField(unique=True,null=True)
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
    department = models.ForeignKey('company_details.Department', on_delete=models.SET_NULL, null=True, blank=True)
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
    




class EmployeeYearlyCalendar(models.Model):
    emp        = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='yearly_calendar')
    year       = models.PositiveIntegerField()
    # Store data for each day in a JSON format, for example: {"2024-01-01": {"status": "Holiday", "remarks": "New Year"}}
    daily_data = models.JSONField(default=dict)  # Stores the daily status, leave type, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('emp', 'year')
        ordering = ['year']

    def __str__(self):
        return f"Yearly Calendar for {self.emp} - {self.year}"

    def populate_calendar(self, holidays, weekends, attendance, leave_requests):
        """
        Populate the calendar with holidays, weekends, attendance, and leave requests.
        """
        start_date = date(self.year, 1, 1)
        end_date = date(self.year, 12, 31)

        current_date = start_date
        while current_date <= end_date:
            # Set initial status
            day_status = 'Work'
            remarks = None
            leave_type = None

            # Check if it's a holiday
            if current_date in holidays:
                day_status = 'Holiday'
                remarks = 'Holiday'

            # Check if it's a weekend
            elif any(weekend.is_weekend(current_date) for weekend in weekends):
                day_status = 'Weekend'
                remarks = 'Weekend'

            # Check if leave is approved for the day
            elif any(l.start_date <= current_date <= l.end_date and l.status == 'Approved' for l in leave_requests):
                day_status = 'Leave'
                leave_type = next((l.leave_type.name for l in leave_requests if l.start_date <= current_date <= l.end_date and l.status == 'Approved'), None)
                remarks = f"Leave: {leave_type}"

            # Check attendance
            elif any(a.date == current_date for a in attendance):
                day_status = 'Present'
                remarks = 'Attended'

            # Populate the daily data
            self.daily_data[str(current_date)] = {
                'status': day_status,
                'remarks': remarks,
                'leave_type': leave_type
            }

            current_date += timedelta(days=1)

        self.save()

