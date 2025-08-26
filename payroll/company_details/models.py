from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from datetime import datetime, timedelta
import calendar
from django.db.models.signals import m2m_changed
from employee_details.models import Employee,EmployeeSalaryStructure,PayrollRun,Payslip,PayslipComponent
from django.contrib.auth.models import User


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# Create your models here.
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=100)
    employer_name = models.CharField(max_length=100)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name=models.CharField(max_length=20,unique=True)
    company=models.ForeignKey(Company,on_delete=models.CASCADE)

class Role(models.Model):
    role_name=models.CharField(max_length=50,unique=True)
    
# WWWWWWWWWWW
