from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SalaryComponent, EmployeeSalaryStructure, Employee
from simpleeval import simple_eval

@receiver(post_save, sender=SalaryComponent)
def update_formula_components(sender, instance, **kwargs):
    if instance.for_formula and instance.formula:
        employees = Employee.objects.all()
        for emp in employees:
            # Build context of available components for this employee
            context = {}
            for comp in EmployeeSalaryStructure.objects.filter(employee=emp, is_active=True):
                context[comp.component.code] = float(comp.amount or 0)

            try:
                value = simple_eval(instance.formula, names=context)
            except Exception:
                value = 0

            # Update or create the EmployeeSalaryStructure
            EmployeeSalaryStructure.objects.update_or_create(
                employee=emp,
                component=instance,
                defaults={"amount": value, "is_active": True}
            )

@receiver(post_delete, sender=SalaryComponent)
def delete_employee_component(sender, instance, **kwargs):
    EmployeeSalaryStructure.objects.filter(component=instance).delete()
