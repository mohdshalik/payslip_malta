from django.shortcuts import render

# Create your views here.
from rest_framework import status,generics,viewsets,permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.response import Response
import datetime
from .models import SalaryComponent,EmployeeSalaryStructure,Payslip,PayslipComponent,Employee,Role,PayrollRun
from .serializer import SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayslipSerializer,PaySlipComponentSerializer,PayrollRunSerializer
# Create your views here.
class SalaryComponentViewSet(viewsets.ModelViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class EmployeeSalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSalaryStructure.objects.all()
    serializer_class = EmployeeSalaryStructureSerializer


# class PayrollFormulaViewSet(viewsets.ModelViewSet):
#     queryset = PayrollFormula.objects.all()
#     serializer_class = PayrollFormulaSerializer

class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer

    # @action(detail=False, methods=['get'],
    #         url_path='employee/(?P<emp_code>[^/.]+)/download/(?P<year>\d{4})/(?P<month>\d{1,2})')
    # def download_employee_payslip_by_month(self, request, emp_code=None, year=None, month=None):
    #     """Download a payslip for a specific employee for a given month and year."""
    #     try:
    #         # Ensure month is an integer between 1 and 12
    #         month = int(month)
    #         year = int(year)
    #         if not 1 <= month <= 12:
    #             return Response({"error": "Month must be between 1 and 12"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Calculate the start and end dates for the given month/year
    #         start_date = datetime.date(year=year, month=month, day=1)
    #         if month == 12:
    #             end_date = datetime.date(year=year + 1, month=1, day=1) - datetime.timedelta(days=1)
    #         else:
    #             end_date = datetime.date(year=year, month=month + 1, day=1) - datetime.timedelta(days=1)
    #
    #         # Fetch the employee by emp_code
    #         try:
    #             employee = Employee.objects.get(emp_code=emp_code)
    #         except Employee.DoesNotExist:
    #             return Response(
    #                 {"error": f"No employee found with emp_code {emp_code}"},
    #                 status=status.HTTP_404_NOT_FOUND
    #             )
    #
    #         # Fetch the payslip for the employee and date range
    #         payslip = Payslip.objects.get(
    #             employee=employee,
    #             payroll_run__start_date=start_date,
    #             payroll_run__end_date=end_date
    #         )
    #         return generate_payslip_pdf(request, payslip)
    #     except Payslip.DoesNotExist:
    #         return Response(
    #             {"error": f"No payslip found for employee {emp_code} for {month}/{year}"},
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    #     except ValueError:
    #         return Response({"error": "Invalid year or month format"}, status=status.HTTP_400_BAD_REQUEST)
    #
    # @action(detail=False, methods=['get'],
    #         url_path='employee/(?P<employee_id>\d+)/filter/(?P<year>\d{4})/(?P<month>\d{1,2})')
    # def filter_employee_payslip_by_month(self, request, employee_id=None, year=None, month=None):
    #     """Retrieve payslip data for a specific employee for a given month and year."""
    #     try:
    #         # Ensure month is an integer between 1 and 12
    #         month = int(month)
    #         year = int(year)
    #         if not 1 <= month <= 12:
    #             return Response({"error": "Month must be between 1 and 12"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Calculate the start and end dates for the given month/year
    #         start_date = datetime.date(year=year, month=month, day=1)
    #         if month == 12:
    #             end_date = datetime.date(year=year + 1, month=1, day=1) - datetime.timedelta(days=1)
    #         else:
    #             end_date = datetime.date(year=year, month=month + 1, day=1) - datetime.timedelta(days=1)
    #
    #         # Fetch the payslip for the employee and date range
    #         payslip = Payslip.objects.get(
    #             employee_id=employee_id,
    #             payroll_run__start_date=start_date,
    #             payroll_run__end_date=end_date
    #         )
    #         serializer = self.get_serializer(payslip)
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     except Payslip.DoesNotExist:
    #         return Response(
    #             {"error": f"No payslip found for employee {employee_id} for {month}/{year}"},
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    #     except ValueError:
    #         return Response({"error": "Invalid year or month format"}, status=status.HTTP_400_BAD_REQUEST)
    #

class PayslipComponentViewSet(viewsets.ModelViewSet):
    queryset = PayslipComponent.objects.all()
    serializer_class = PaySlipComponentSerializer


class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer


