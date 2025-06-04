from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from datetime import datetime, timedelta
import calendar
from django.db.models.signals import m2m_changed
from employee_details.models import Employee,EmployeeSalaryStructure,PayrollRun,Payslip,PayslipComponent,EmployeeYearlyCalendar
from django.contrib.auth.models import User


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# Create your models here.
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name=models.CharField(max_length=20,unique=True)
    company=models.ForeignKey('Company',on_delete=models.CASCADE)

class Role(models.Model):
    role_name=models.CharField(max_length=50,unique=True)
    
# WWWWWWWWWWW
#weekend
#hhhhhhhhhh
#holiday
class weekend_calendar(models.Model):
    DAY_TYPE_CHOICES = [
        ('leave', 'Leave'),
        ('fullday', 'fullday'),
        ('halfday', 'Halfday'),
    ]
    description       = models.TextField()
    calendar_code     = models.CharField(max_length=100)
    year              = models.PositiveIntegerField()
    monday            = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    tuesday           = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    wednesday         = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    thursday          = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    friday            = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    saturday          = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    sunday            = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    created_at        = models.DateTimeField(auto_now_add=True)
    created_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    def __str__(self):
        return f"{self.calendar_code} - {self.year}"
    def is_weekend(self, date):
        """Check if the given date is a weekend based on the calendar configuration."""
        day_name = date.strftime('%A').lower()
        print("dayyy",day_name)
        day_type = getattr(self, day_name, 'fullday')
        return day_type == 'leave'
    def get_weekend_days(self):
        """Return list of day names that are marked as 'leave'."""
        days = {
            'Monday': self.monday,
            'Tuesday': self.tuesday,
            'Wednesday': self.wednesday,
            'Thursday': self.thursday,
            'Friday': self.friday,
            'Saturday': self.saturday,
            'Sunday': self.sunday,
        }
        return [day for day, value in days.items() if value == 'leave']
    def __str__(self):
        return f"{self.calendar_code} - {self.year}"
class WeekendDetail(models.Model):
    WEEKDAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    DAY_TYPE_CHOICES = [
        ('leave', 'Leave'),
        ('fullday', 'Full Day'),
        ('halfday', 'Half Day'),
    ]
    weekend_calendar = models.ForeignKey(weekend_calendar, related_name='details', on_delete=models.CASCADE)
    weekday          = models.CharField(max_length=9, choices=WEEKDAY_CHOICES)
    day_type         = models.CharField(max_length=7, choices=DAY_TYPE_CHOICES)
    week_of_month    = models.PositiveIntegerField(null=True, blank=True)  # 1 to 5 for specifying specific weeks
    month_of_year    = models.PositiveIntegerField(null=True, blank=True)
    date             = models.DateField(null=True, blank=True)  # Specific date for the day
    created_at       = models.DateTimeField(auto_now_add=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    class Meta:
        ordering = [ 'pk']
@receiver(post_save, sender=weekend_calendar)
def create_weekend_details(sender, instance, created, **kwargs):
    if created:
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_types = {
            'monday': instance.monday,
            'tuesday': instance.tuesday,
            'wednesday': instance.wednesday,
            'thursday': instance.thursday,
            'friday': instance.friday,
            'saturday': instance.saturday,
            'sunday': instance.sunday,
        }

        year = instance.year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        delta = timedelta(days=1)

        while start_date <= end_date:
            weekday_name = calendar.day_name[start_date.weekday()].lower()
            WeekendDetail.objects.create(
                weekend_calendar=instance,
                weekday=weekday_name.capitalize(),
                day_type=day_types[weekday_name],
                week_of_month=(start_date.day - 1) // 7 + 1,
                month_of_year=start_date.month,
                date=start_date.date()
            )
            start_date += delta

    def __str__(self):
        return f"{self.weekday} - {self.day_type}"

class assign_weekend(models.Model):
    EMP_CHOICES = [
        ("branch", "Branch"),
        ("department", "Department"),
        ("category", "Category"),
        ("employee", "Employee"),
    ]
    related_to    = models.CharField(max_length=20, choices=EMP_CHOICES,null=True)
    Company        = models.ManyToManyField(Company,  null=True, blank=True)
    department    = models.ManyToManyField(Department,  null=True, blank=True)
    category      = models.ManyToManyField(Role, null=True, blank=True)
    employee      = models.ManyToManyField(Employee,  null=True, blank=True)
    weekend_model = models.ForeignKey(weekend_calendar,on_delete=models.CASCADE)
    created_at    = models.DateTimeField(auto_now_add=True)
    created_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')


@receiver(m2m_changed, sender=assign_weekend.Company.through)
def update_branch_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "Company":
        branches = instance.branch.all()
        logger.debug(f"Updating employees for branches: {[branch.id for branch in branches]}")
        for branch in branches:
            updated_count = Employee.objects.filter(emp_branch_id=branch.id).update(emp_weekend_calendar=instance.weekend_model)
            logger.debug(f"Updated {updated_count} employees for branch ID {branch.id}")

@receiver(m2m_changed, sender=assign_weekend.department.through)
def update_department_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "department":
        departments = instance.department.all()
        logger.debug(f"Updating employees for departments: {[department.id for department in departments]}")
        for department in departments:
            updated_count = Employee.objects.filter(emp_dept_id=department.id).update(emp_weekend_calendar=instance.weekend_model)
            logger.debug(f"Updated {updated_count} employees for department ID {department.id}")

# @receiver(m2m_changed, sender=assign_weekend.category.through)
# def update_category_weekend_calendar(sender, instance, action, **kwargs):
#     if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "category":
#         categories = instance.category.all()
#         logger.debug(f"Updating employees for categories: {[category.id for category in categories]}")
#         for category in categories:
#             updated_count = Employee.objects.filter(emp_ctgry_id=category.id).update(emp_weekend_calendar=instance.weekend_model)
#             logger.debug(f"Updated {updated_count} employees for category ID {category.id}")

@receiver(m2m_changed, sender=assign_weekend.employee.through)
def update_employee_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "employee":
        employees = instance.employee.all()
        logger.debug(f"Updating employees: {[employee.id for employee in employees]}")
        for employee in employees:
            employee.emp_weekend_calendar = instance.weekend_model
            employee.save()
            logger.debug(f"Updated employee ID {employee.id}")
def update_employee_yearly_calendar(employee, weekend_model):
    year = weekend_model.year
    # Check if EmployeeYearlyCalendar for this employee and year already exists
    try:
        yearly_calendar = EmployeeYearlyCalendar.objects.get(emp=employee, year=year)
        logger.debug(f"Found existing EmployeeYearlyCalendar for employee ID {employee.id} for year {year}")
    except EmployeeYearlyCalendar.DoesNotExist:
        yearly_calendar = EmployeeYearlyCalendar(emp=employee, year=year, daily_data={})
        logger.debug(f"Created new EmployeeYearlyCalendar for employee ID {employee.id} for year {year}")

    # Merge new weekend details into existing `daily_data` without overwriting existing data
    weekend_details = WeekendDetail.objects.filter(weekend_calendar=weekend_model)
    updated_data = yearly_calendar.daily_data  # Copy of existing data

    for detail in weekend_details:
        date_str = detail.date.strftime("%Y-%m-%d")
        # Only add or update if the date is not already set or if you need to update existing data
        if date_str not in updated_data or updated_data[date_str].get("status") != "Leave":
            updated_data[date_str] = {
                "status": "Leave" if detail.day_type == 'leave' else detail.day_type,
                "remarks": "Weekend assigned"
            }

    # Save the updated or newly created yearly calendar with merged data
    yearly_calendar.daily_data = updated_data
    yearly_calendar.save()
    logger.debug(f"Updated EmployeeYearlyCalendar for employee ID {employee.id} with new weekend data")

class holiday_calendar(models.Model):
    calendar_title  = models.CharField(max_length=50)
    year            = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    
    def __str__(self):
        return f"{self.calendar_title} - {self.year}"
    def is_holiday(self, date):
        # Logic to determine if 'date' is a holiday
        return self.holidays.filter(holiday_date=date).exists()
    # holiday         = models.ManyToManyField(holiday)

class holiday(models.Model):
    description = models.CharField(max_length=50,unique=True)
    start_date  = models.DateField()
    end_date    = models.DateField()
    calendar    = models.ForeignKey(holiday_calendar,on_delete=models.CASCADE,null=True,related_name='holiday_list')
    restricted  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')



class assign_holiday(models.Model):
    EMP_CHOICES = [
        ("branch", "Branch"),
        ("department", "Department"),
        ("category", "Category"),
        ("employee", "Employee"),
    ]
    related_to     = models.CharField(max_length=20, choices=EMP_CHOICES,null=True)
    company        = models.ManyToManyField(Company,  null=True, blank=True)
    department    = models.ManyToManyField(Department,  null=True, blank=True)
    category      = models.ManyToManyField(Role, null=True, blank=True)
    employee      = models.ManyToManyField(Employee,  null=True, blank=True)
    weekend_model = models.ForeignKey(weekend_calendar,on_delete=models.CASCADE)
    created_at    = models.DateTimeField(auto_now_add=True)
    created_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')



@receiver(m2m_changed, sender=assign_holiday.company.through)
def update_company_holiday_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "company":
        companies = instance.company.all()
        # logger.debug(f"Updating employees for branches: {[branch.id for branch in branches]}")
        for company in companies:
            updated_count = Employee.objects.filter(company=company.id).update(holiday_calendar=instance.holiday_model)
            # logger.debug(f"Updated {updated_count} employees for branch ID {branch.id}")
@receiver(m2m_changed, sender=assign_weekend.department.through)
def update_department_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "department":
        departments = instance.department.all()
        # logger.debug(f"Updating employees for departments: {[department.id for department in departments]}")
        for department in departments:
            updated_count = Employee.objects.filter(emp_dept_id=department.id).update(holiday_calendar=instance.holiday_model)
            # logger.debug(f"Updated {updated_count} employees for department ID {department.id}")
@receiver(m2m_changed, sender=assign_weekend.category.through)
def update_category_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "category":
        categories = instance.category.all()
        # logger.debug(f"Updating employees for categories: {[category.id for category in categories]}")
        for category in categories:
            updated_count = Employee.objects.filter(emp_ctgry_id=category.id).update(holiday_calendar=instance.holiday_model)
            # logger.debug(f"Updated {updated_count} employees for category ID {category.id}")
@receiver(m2m_changed, sender=assign_holiday.employee.through)
def update_employee_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "employee":
        employees = instance.employee.all()
        # logger.debug(f"Updating employees: {[employee.id for employee in employees]}")
        for employee in employees:
            employee.holiday_calendar = instance.holiday_model
            employee.save()
            # logger.debug(f"Updated employee ID {employee.id}")
def update_employee_yearly_calendar_with_holidays(employee, holiday_calendar):
    year = holiday_calendar.year
    print("holiday")
    try:
        yearly_calendar, created = EmployeeYearlyCalendar.objects.get_or_create(emp=employee, year=year)
        updated_data = yearly_calendar.daily_data
        for holiday in holiday_calendar.holiday.all():
            current_date = holiday.start_date
            while current_date <= holiday.end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                # Only add holiday data if not already set or if replacing certain data is allowed
                if date_str not in updated_data or updated_data[date_str].get("status") != "Leave":
                    updated_data[date_str] = {
                        "status": "Leave" if holiday.restricted else "Holiday",
                        "remarks": holiday.description
                    }
                current_date += timedelta(days=1)
        print("holiday1")
        yearly_calendar.daily_data = updated_data
        yearly_calendar.save()

    except Exception as e:
        logger.error(f"Failed to update EmployeeYearlyCalendar for employee ID {employee.id}: {e}")
