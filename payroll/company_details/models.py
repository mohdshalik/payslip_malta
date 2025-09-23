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
class FS5Form(models.Model):
    # Section A - Payer Information
    business_name = models.CharField(max_length=255)
    business_address = models.TextField()
    locality = models.CharField(max_length=255, blank=True, null=True)
    postcode = models.CharField(max_length=10, blank=True, null=True)
    telephone_number = models.CharField(max_length=20, blank=True, null=True)
    fax_number = models.CharField(max_length=20, blank=True, null=True)

    payer_pe_no = models.CharField(max_length=20)
    payment_month = models.PositiveSmallIntegerField()
    payment_year = models.PositiveSmallIntegerField()

    # Section B - Number of Payees
    number_of_payees_main = models.IntegerField(default=0)  # B1
    number_of_payees_part_time = models.IntegerField(default=0)  # B2

    # Section C - Gross Emoluments
    gross_emoluments_main = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # C1
    overtime = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # C1A
    gross_emoluments_part_time = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # C2
    taxable_fringe_benefits = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # C3
    total_gross_emoluments = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # C4

    # Section D - Tax Deductions & SSC
    tax_deductions_main = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D1
    tax_deductions_overtime = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D1A
    tax_deductions_part_time = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D2
    tax_arrears_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D3
    total_tax_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D4
    social_security_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D5
    maternity_fund_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D5A
    total_due_commissioner = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # D6

    # Section E - Payment Details
    date_of_payment = models.DateField(blank=True, null=True)
    total_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cheque_bank = models.CharField(max_length=255, blank=True, null=True)  # E2
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    branch = models.CharField(max_length=50, blank=True, null=True)
    bank_account_no = models.CharField(max_length=50, blank=True, null=True)  # E3

    person_paying = models.CharField(max_length=255, blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)

    # For official use (optional, may not be filled by payer)
    receipt_no = models.CharField(max_length=50, blank=True, null=True)
    date_received = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FS5 - {self.business_name} ({self.payment_month}/{self.payment_year})"
