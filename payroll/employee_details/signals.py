from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payslip,SalaryComponent,EmployeeSalaryStructure,Employee
from django.apps import apps
import logging
logger = logging.getLogger(__name__)
def evaluate_formula(formula, variables):
    """
    Evaluate formula by replacing variables with component values.
    """
    try:
        logger.debug(f"Evaluating formula: {formula} with variables: {variables}")
        formula = formula.strip("'")
        for key, value in variables.items():
            formula = formula.replace(key, str(value))
        logger.debug(f"Formula after substitution: {formula}")
        result = eval(formula)
        return round(result, 2)
    except Exception as e:
        logger.error(f"Error evaluating formula '{formula}': {e}")
        return 0
@receiver(post_save, sender=SalaryComponent)
def update_employee_salary_structure(sender, instance, created, **kwargs):
    """
    When a SalaryComponent is created or updated, calculate and store the amount
    in EmployeeSalaryStructure for all employees if is_fixed=False.
    """
    if not instance.is_fixed and instance.formula:  # Only for variable components with a formula
        # Get the EmpMaster model dynamically
        employees = Employee.objects.all()

        for employee in employees:
            # Fetch all existing salary components for this employee to use in formula
            salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            component_amounts = {}

            # Populate fixed component amounts for formula evaluation
            for sc in salary_components:
                if sc.component.is_fixed and sc.amount is not None:
                    component_amounts[sc.component.code] = float(sc.amount)
                    logger.info(f"Using fixed component {sc.component.name} ({sc.component.code}): {sc.amount}")

            # Calculate the amount using the formulag
            amount = evaluate_formula(instance.formula, component_amounts)
            logger.info(f"Calculated amount for {instance.name} ({instance.code}) for employee {employee}: {amount}")

            # Update or create the EmployeeSalaryStructure entry
            EmployeeSalaryStructure.objects.update_or_create(
                employee=employee,
                component=instance,
                defaults={
                    'amount': amount,
                    'is_active': True,
                }
            )
            logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {instance.name} - Amount: {amount}")

