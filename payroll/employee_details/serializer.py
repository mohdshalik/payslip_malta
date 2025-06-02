from rest_framework import serializers
from . models import Employee,SalaryComponent,Payslip,PayrollRun,EmployeeSalaryStructure,Role,PayslipComponent,Role

class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
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
    class Meta:
        model = PayslipComponent
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    payroll_run = PayrollRunSerializer(read_only=True)
    employee = serializers.StringRelatedField()  # Displays employee's string representation
    components = PaySlipComponentSerializer(many=True, read_only=True)  # Include related components

    class Meta:
        model = Payslip
        fields = '__all__'



class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = '__all__'