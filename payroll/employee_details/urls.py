from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . views import SalaryComponentViewSet,EmployeeSalaryStructureViewSet,PayrollRunViewSet,PayslipViewSet,PayslipComponentViewSet,EmployeeViewSet,RoleViewSet
router = DefaultRouter()

# router = DefaultRouter()
router.register(r'employee', EmployeeViewSet)
router.register(r'Role', RoleViewSet)
router.register(r'salarycomponent', SalaryComponentViewSet)
router.register(r'employeesalary', EmployeeSalaryStructureViewSet)
router.register(r'PayrollRun', PayrollRunViewSet)
# router.register(r'PayrollFormula', PayrollFormulaViewSet)
router.register(r'payslip', PayslipViewSet)
router.register(r'PayslipComponent', PayslipComponentViewSet)



urlpatterns = [
    path('', include(router.urls)),
]