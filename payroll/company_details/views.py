from django.shortcuts import render
from  .models import Company,Department,Role
from django.contrib.auth.models import User
from .serializer import CompanySerialiazer,DepartmentSerialiazer,UserSerializer,RoleSerializer
from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer



class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerialiazer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerialiazer


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

# class FS5ReportViewSet(viewsets.ModelViewSet):
#     queryset = FS5Form.objects.all()
#     serializer_class = FS5FormSerializer
