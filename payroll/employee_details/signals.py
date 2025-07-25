from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payslip,SalaryComponent,EmployeeSalaryStructure,Employee,PayslipComponent,PayrollRun
from django.apps import apps
import logging
from simpleeval import SimpleEval, NameNotDefined, FunctionNotDefined
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Q
import decimal
from calendar import monthrange 

# from .models import 

logger = logging.getLogger(__name__)


def evaluate_formula(formula, variables, employee, component):
    try:
        logger.debug(f"Evaluating formula: {formula} with variables: {variables} for employee: {employee}")
        formula = formula.strip("'")

        s = SimpleEval()
        s.names = variables  # ✅ Set variables here

        s.operators.update({
            '<': lambda x, y: x < y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            'and': lambda x, y: x and y,
            'or': lambda x, y: x or y,
            'not': lambda x: not x,
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '%': lambda x, y: x % y
        })

        s.functions.update({
            'MAX': max,
            'MIN': min,
            'AVG': lambda *args: sum(args) / len(args) if args else 0,
            'SUM': sum,
            'ROUND': round
        })

        result = s.eval(formula)  # ✅ No keyword argument here
        return round(float(result), 2)

    except (NameNotDefined, FunctionNotDefined) as e:
        logger.error(f"Invalid variable or function in formula '{formula}' for employee {employee}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error evaluating formula '{formula}' for employee {employee}: {e}")
        return 0
@receiver(post_save, sender=SalaryComponent)
def update_employee_salary_structure(sender, instance, created, **kwargs):
    if not instance.is_fixed and instance.formula:
        EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        EmployeeSalaryStructure = apps.get_model('PayrollManagement', 'EmployeeSalaryStructure')
        employees = EmpMaster.objects.all()

        for employee in employees:
            # Get variables including fixed components, calendar_days, ot_hours etc.
            # variables = get_formula_variables(employee)

            try:
                amount = evaluate_formula(instance.formula, employee, instance)
            except Exception as e:
                logger.error(f"Formula evaluation error for {employee}: {e}")
                amount = Decimal('0.00')

            logger.info(f"Calculated amount for {instance.name} ({instance.code}) for employee {employee}: {amount}")

            EmployeeSalaryStructure.objects.update_or_create(
                employee=employee,
                component=instance,
                defaults={'amount': amount, 'is_active': True}
            )
            logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {instance.name} - Amount: {amount}")



# def daterange(start_date, end_date):
#     for n in range(int((end_date - start_date).days) + 1):
#         yield start_date + timedelta(n)
# def get_worked_days(employee, start_date, end_date):
#     """
#     Calculate worked days considering:
#     - Present days (with attendance records)
#     - Holidays/weekends marked as present
#     - If no attendance data, assume all days worked
#     """
#     # Get all dates in period
#     all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
#     total_days = len(all_dates)
    
#     # Get attendance records
#     attendance_records = Attendance.objects.filter(
#         employee=employee,
#         date__range=(start_date, end_date)
#     )
    
#     # If no attendance data, assume all days worked
#     if not attendance_records.exists():
#         return total_days
    
#     # Calculate present days (including holidays/weekends if marked present)
#     present_days = attendance_records.filter(
#         Q(check_in_time__isnull=False) & 
#         Q(check_out_time__isnull=False)
#     ).count()
    
#     return present_days




def get_formula_variables(employee, start_date=None, end_date=None):
    """Collect all available variables for formula evaluation"""
    if not start_date or not end_date:
        today = datetime.now().date()
        start_date = today.replace(day=1)
        end_date = today.replace(day=monthrange(today.year, today.month)[1])
    
    # Calculate worked days (new logic)
    # worked_days = get_worked_days(employee, start_date, end_date)
    calendar_days = (end_date - start_date).days + 1
    
    variables = {
        # Time-related variables (updated names)
        'calendar_days': Decimal(calendar_days),
        # 'worked_days': Decimal(worked_days),
        'standard_hours': Decimal('160.0'),
        
        # Employee attributes
        # 'employee.grade': str(employee.job_title.grade if hasattr(employee.job_title, 'grade') else ''),
        # 'employee.employee_type': str(employee.employee_type if hasattr(employee, 'employee_type') else ''),
        'employee.joining_date': employee.hired_date.strftime('%Y-%m-%d'),
        'years_of_service': relativedelta(end_date, employee.hired_date).years,
    }
    
    #d all fixed salary components
    fixed_components = EmployeeSalaryStructure.objects.filter(
        employee=employee,
        component__is_fixed=True,
        is_active=True
    )
    for comp in fixed_components:
        if comp.component.code:
            variables[comp.component.code] = comp.amount
    
    return variables



# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.apps import apps
# from calendar import monthrange
# from datetime import datetime
# from decimal import Decimal
# import logging

# logger = logging.getLogger(__name__)

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from calendar import monthrange
# from .models import PayrollRun, Payslip, EmployeeSalaryStructure, PayslipComponent, SalaryComponent


# @receiver(post_save, sender=PayrollRun)
# def generate_payslips_for_payroll_run(sender, instance, created, **kwargs):
#     if not created:
#         return  # Only run on creation

#     # Step 1: Get employees (filtered by department if applicable)
#     employees = instance.get_employees()
    
#     # Get total days in the payroll month
#     _, total_days_in_month = monthrange(instance.year, instance.month)

#     for employee in employees:
#         salary_structures = EmployeeSalaryStructure.objects.filter(
#             employee=employee,
#             is_active=True
#         )

#         gross_salary = 0
#         total_deductions = 0

#         # Create payslip first
#         payslip = Payslip.objects.create(
#             payroll_run=instance,
#             employee=employee,
#             total_working_days=total_days_in_month,
#             days_worked=total_days_in_month  # You can update this from attendance logic later
#         )

#         # Process each component
#         for structure in salary_structures:
#             component = structure.component
#             amount = structure.amount or 0

#             # Add component to payslip
#             PayslipComponent.objects.create(
#                 payslip=payslip,
#                 component=component,
#                 amount=amount
#             )

#             if component.component_type == 'addition':
#                 gross_salary += amount
#             elif component.component_type == 'deduction':
#                 total_deductions += amount

#         # Final net salary
#         net_salary = gross_salary - total_deductions

#         # Update payslip
#         payslip.gross_salary = gross_salary
#         payslip.total_deductions = total_deductions
#         payslip.total_additions = gross_salary  # Since it's sum of additions
#         payslip.net_salary = net_salary
#         payslip.save()


# @receiver(post_save, sender=EmployeeSalaryStructure)
# def update_dependent_salary_components(sender, instance, created, **kwargs):
#     """
#     When an EmployeeSalaryStructure's amount is updated, recalculate amounts for
#     other components that use this component in their formulas.
#     """
#     # Only proceed if the amount was updated (not created) and the component is fixed
#     if created or not instance.component.is_fixed:
#         return

#     # Get the EmpMaster model dynamically
#     EmpMaster = apps.get_model('EmpManagement', 'emp_master')
    
#     # Get all employees to update their dependent components
#     employees = EmpMaster.objects.all()

#     # Find all variable SalaryComponents that might depend on this component
#     dependent_components = SalaryComponent.objects.filter(
#         is_fixed=False,
#         formula__contains=instance.component.code  # Check if the updated component's code appears in the formula
#     )

#     for employee in employees:
#         # Fetch all salary components for this employee to use in formula evaluation
#         salary_components = EmployeeSalaryStructure.objects.filter(employee=employee)
#         component_amounts = {}

#         # Populate fixed component amounts for formula evaluation
#         for sc in salary_components:
#             if sc.component.is_fixed and sc.amount is not None:
#                 component_amounts[sc.component.code] = float(sc.amount)
#                 logger.info(f"Using fixed component {sc.component.name} ({sc.component.code}): {sc.amount}")

#         # Recalculate amounts for dependent components
#         for component in dependent_components:
#             # Calculate the new amount using the formula
#             amount = evaluate_formula(component.formula, component_amounts)
#             logger.info(f"Calculated amount for {component.name} ({component.code}) for employee {employee}: {amount}")

#             # Update or create the EmployeeSalaryStructure entry for the dependent component
#             EmployeeSalaryStructure.objects.update_or_create(
#                 employee=employee,
#                 component=component,
#                 defaults={
#                     'amount': amount,
#                     'is_active': True,
#                 }
#             )
#             logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {component.name} - Amount: {amount}")