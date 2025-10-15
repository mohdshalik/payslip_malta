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
import os
import zipfile
from io import BytesIO
from django.http import FileResponse, HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

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
    @action(detail=False, methods=['get'], url_path='download-fs5')
    def download_fs5_report(self, request):
        """
        Download FS5 PDFs by month/year or for a specific employee.
        Example:
        /api/payrollrun/download-fs5/?month=9&year=2025
        /api/payrollrun/download-fs5/?month=9&year=2025&employee_id=3
        """
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        emp_id = request.query_params.get('employee_id')

        if not month or not year:
            return Response({'error': 'Please provide month and year (e.g., ?month=9&year=2025)'}, status=400)

        # Build directory
        fs5_dir = os.path.join(settings.MEDIA_ROOT, "fs5")
        if not os.path.exists(fs5_dir):
            return Response({'error': 'No FS5 files found.'}, status=404)

        # Collect files
        files_to_zip = []
        for file_name in os.listdir(fs5_dir):
            if f"_{month}_{year}" in file_name:
                if emp_id:
                    if f"FS5_{emp_id}_" in file_name or file_name.startswith(f"FS5_{emp_id}"):
                        files_to_zip.append(os.path.join(fs5_dir, file_name))
                else:
                    files_to_zip.append(os.path.join(fs5_dir, file_name))

        if not files_to_zip:
            return Response({'error': 'No FS5 files found for the given criteria.'}, status=404)

        # If only one file → return directly
        if len(files_to_zip) == 1:
            file_path = files_to_zip[0]
            return FileResponse(open(file_path, 'rb'), content_type='application/pdf')

        # If multiple files → zip them
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files_to_zip:
                zip_file.write(file_path, os.path.basename(file_path))
        zip_buffer.seek(0)

        zip_name = f"FS5_{month}_{year}.zip"
        response = HttpResponse(zip_buffer, content_type="application/zip")
        response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
        return response

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
    # @action(detail=True, methods=['get'], url_path='download-fs5')
    # def download_fs5(self, request, pk=None):
    #     payroll_run = self.get_object()
    #     company = payroll_run.get_employees().first().company
    #     file_path = os.path.join(settings.MEDIA_ROOT, "fs5", f"FS5_{company.name}_{payroll_run.month}_{payroll_run.year}.pdf")
    #     if os.path.exists(file_path):
    #         return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    #     return Response({'error': 'FS5 file not found'}, status=404)
    # @action(detail=True, methods=["get"])
    # def fs5_zip(self, request, pk=None):
    #     payroll_run = self.get_object()

    #     # ensure payslips exist
    #     payslips = payroll_run.payslips.all()
    #     if not payslips.exists():
    #         return Response({"error": "No payslips found for this run"}, status=404)

    #     # temp zip file path
    #     zip_path = os.path.join(
    #         settings.MEDIA_ROOT,
    #         f"fs5_zip/PayrollRun_{payroll_run.id}_FS5.zip"
    #     )
    #     os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    #     with zipfile.ZipFile(zip_path, "w") as zipf:
    #         for payslip in payslips:
    #             if payslip.fs5_pdf:
    #                 file_path = payslip.fs5_pdf.path
    #                 arcname = os.path.basename(file_path)
    #                 zipf.write(file_path, arcname=arcname)

    #     return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=os.path.basename(zip_path))



