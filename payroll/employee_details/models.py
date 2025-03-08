from django.db import models

# Create your models here.
class Role(models.Model):
    role_name=models.CharField(max_length=50,unique=True)
    

class Employee(models.Model):
    company = models.ForeignKey('company_details.Company', on_delete=models.CASCADE, related_name='employees')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=100 )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    hire_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"