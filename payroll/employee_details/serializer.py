from rest_framework import serializers
from . models import Employee,SalaryComponent,Payslip,PayrollRun,EmployeeSalaryStructure,PayslipComponent,category,FS5Report
from company_details.models import Role,Company
from company_details.serializer import CompanySerialiazer,RoleSerializer

class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'

class categorytSerializer(serializers.ModelSerializer):
    class Meta:
        model = category
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=category.objects.all())
    job_title = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = Employee
        fields = '__all__'
    def to_representation(self, instance):
        """Customize output to show nested details"""
        representation = super().to_representation(instance)
        representation['company'] = CompanySerialiazer(instance.company).data
        representation['category'] = categorytSerializer(instance.category).data
        representation['job_title'] = RoleSerializer(instance.job_title).data
        return representation
class EmployeeSalaryStructureSerializer(serializers.ModelSerializer):
    emp_code = serializers.SerializerMethodField()  # Field for emp_code from emp_master
    component_name = serializers.SerializerMethodField()  # Field for name from SalaryComponent

    class Meta:
        model = EmployeeSalaryStructure
        fields = '__all__'  # Include all fields from the model
        # Optionally, explicitly list fields to include emp_code and component_name
        # fields = ['id', 'employee', 'component', 'amount', 'is_active', 'date_created', 'date_updated', 'emp_code', 'component_name']

    def get_emp_code(self, obj):
        return obj.employee.emp_code  # Fetch emp_code from the related emp_master

    def get_component_name(self, obj):
        return obj.component.name  # Fetch name from the related SalaryComponent

    def to_representation(self, instance):
        """
        Customize the output to replace employee and component IDs with emp_code and component_name.
        """
        rep = super().to_representation(instance)
        rep['employee'] = self.get_emp_code(instance)  # Replace employee ID with emp_code
        rep['component'] = self.get_component_name(instance)  # Replace component ID with name
        return rep


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'


class PaySlipComponentSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='component.name', read_only=True)
    component_type = serializers.CharField(source='component.component_type', read_only=True)
    class Meta:
        model = PayslipComponent
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    payroll_run = PayrollRunSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True) 
    components = PaySlipComponentSerializer(many=True, read_only=True)  # Include related components

    class Meta:
        model = Payslip
        fields = '__all__'



class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = '__all__'
    

class FS5ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = FS5Report
        fields = '__all__'