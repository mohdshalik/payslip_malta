from django.apps import AppConfig


class EmployeeDetailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employee_details'
    def ready(self):
        import employee_details.signals 
