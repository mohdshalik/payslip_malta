from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import status,generics,viewsets,permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.response import Response
import datetime
from .models import SalaryComponent,EmployeeSalaryStructure,Payslip,PayslipComponent,Employee,PayrollRun,Employee,category
from .serializer import SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayslipSerializer,PaySlipComponentSerializer,PayrollRunSerializer,EmployeeSerializer,categorytSerializer
from company_details.models import Role
from company_details.serializer import RoleSerializer
# Create your views here.

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class categoryViewSet(viewsets.ModelViewSet):
    queryset = category.objects.all()
    serializer_class = categorytSerializer

class SalaryComponentViewSet(viewsets.ModelViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class EmployeeSalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSalaryStructure.objects.all()
    serializer_class = EmployeeSalaryStructureSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['employee']
    search_fields = ['employee__emp_code']

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        data = {}
        qs = self.filter_queryset(self.get_queryset())
        for obj in qs:
            emp_code = obj.employee.emp_code
            if emp_code not in data:
                data[emp_code] = []
            data[emp_code].append(EmployeeSalaryStructureSerializer(obj).data)
        return Response(data)



class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer



class PayslipComponentViewSet(viewsets.ModelViewSet):
    queryset = PayslipComponent.objects.all()
    serializer_class = PaySlipComponentSerializer


class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer
    def perform_create(self, serializer):
        # Save the payroll run and automatically generate payslips
        serializer.save()

    @action(detail=True, methods=['post'], url_path='generate-payslips')
    def generate_payslips(self, request, pk=None):
        payroll_run = self.get_object()
        if payroll_run.status != 'pending':
            return Response({'error': 'Payslips can only be generated for pending payroll runs'}, status=400)
        
        payroll_run.generate_payslips()
        return Response({'status': 'Payslips generated successfully'})


