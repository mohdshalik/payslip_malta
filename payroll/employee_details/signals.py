from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payslip,SalaryComponent,EmployeeSalaryStructure,Employee,PayslipComponent
from django.apps import apps
import logging
from simpleeval import SimpleEval, NameNotDefined, FunctionNotDefined


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
        # EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        EmployeeSalaryStructure = EmployeeSalaryStructure.objects.all()
        employees = Employee.objects.all()

        for employee in employees:
            # Get variables including fixed components, calendar_days, ot_hours etc.
            variables = get_formula_variables(employee)

            try:
                amount = evaluate_formula(instance.formula, variables, employee, instance)
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


@receiver(post_save, sender=EmployeeSalaryStructure)
def update_dependent_salary_components(sender, instance, created, **kwargs):
    """
    When an EmployeeSalaryStructure's amount is updated, recalculate amounts for
    other components that use this component in their formulas.
    """
    # Only proceed if the amount was updated (not created) and the component is fixed
    if created or not instance.component.is_fixed:
        return

    # Get the EmpMaster model dynamically
    # EmpMaster = apps.get_model('EmpManagement', 'emp_master')
    
    # Get all employees to update their dependent components
    employees = Employee.objects.all()

    # Find all variable SalaryComponents that might depend on this component
    dependent_components = SalaryComponent.objects.filter(
        is_fixed=False,
        formula__contains=instance.component.code  # Check if the updated component's code appears in the formula
    )

    for employee in employees:
        # Fetch all salary components for this employee to use in formula evaluation
        salary_components = EmployeeSalaryStructure.objects.filter(employee=employee)
        component_amounts = {}

        # Populate fixed component amounts for formula evaluation
        for sc in salary_components:
            if sc.component.is_fixed and sc.amount is not None:
                component_amounts[sc.component.code] = float(sc.amount)
                logger.info(f"Using fixed component {sc.component.name} ({sc.component.code}): {sc.amount}")

        # Recalculate amounts for dependent components
        for component in dependent_components:
            # Calculate the new amount using the formula
            amount = evaluate_formula(component.formula, component_amounts)
            logger.info(f"Calculated amount for {component.name} ({component.code}) for employee {employee}: {amount}")

            # Update or create the EmployeeSalaryStructure entry for the dependent component
            EmployeeSalaryStructure.objects.update_or_create(
                employee=employee,
                component=component,
                defaults={
                    'amount': amount,
                    'is_active': True,
                }
            )
            logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {component.name} - Amount: {amount}")


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from calendar import monthrange
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='PayrollManagement.PayrollRun')
def run_payroll_on_save(sender, instance, created, **kwargs):
    if not created or instance.status != 'pending':
        return

    EmpMaster = EmpMaster.objects.all()
    SalaryComponent = SalaryComponent.objects.all()
    EmployeeSalaryStructure = EmployeeSalaryStructure.objects.all()
    Payslip = Payslip.objects.all()
    PayslipComponent = PayslipComponent.objects.all()
    try:
        total_working_days = monthrange(instance.year, instance.month)[1]
        start_date = datetime(instance.year, instance.month, 1).date()
        end_date = datetime(instance.year, instance.month, total_working_days).date()
    except Exception as e:
        logger.error(f"Invalid date setup for PayrollRun {instance.id}: {e}")
        return

    employees = EmpMaster.objects.filter(is_active=True)

    for employee in employees:
        # Collect formula variables (working days, attendance etc.)
        variables = get_formula_variables(employee, start_date, end_date)

        salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
        total_additions = Decimal('0.00')
        total_deductions = Decimal('0.00')

        days_worked = variables.get('working_days', 0)
        payslip = Payslip.objects.create(
            payroll_run=instance,
            employee=employee,
            total_working_days=total_working_days,
            days_worked=days_worked,
        )

        for sc in salary_components:
            component = sc.component
            amount = sc.amount or Decimal('0.00')

            if not component.is_fixed and component.formula:
                try:
                    amount = Decimal(str(evaluate_formula(component.formula, variables, employee, component)))
                except Exception as e:
                    logger.error(f"Formula error for {component.name}: {e}")
                    amount = Decimal('0.00')

            PayslipComponent.objects.create(
                payslip=payslip,
                component=component,
                amount=amount
            )

            if component.component_type == 'addition':
                total_additions += amount
            elif component.component_type == 'deduction':
                total_deductions += amount

        # Finalize payslip
        gross_salary = total_additions
        net_salary = gross_salary - total_deductions

        payslip.total_additions = total_additions
        payslip.total_deductions = total_deductions
        payslip.gross_salary = gross_salary
        payslip.net_salary = net_salary
        payslip.save()

    # Update payroll run status
    instance.status = 'processed'
    instance.save(update_fields=['status'])
