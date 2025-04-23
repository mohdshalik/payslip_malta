from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Company,Department


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']  # Expose only safe fields
        read_only_fields = ['id']  # Prevent updating the ID


class CompanySerialiazer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class DepartmentSerialiazer(serializers.ModelSerializer):
    class Meta:
        models = Department
        fields = '__all__'
