from django.db import models
from django.contrib.auth.models import User
from .constants import account_type, gender_type
# Create your models here.

class UserBankAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    account_type = models.CharField(max_length=10, choices=account_type)
    account_number = models.IntegerField(unique=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=gender_type)
    initial_deposit_date = models.DateField(auto_now_add=True)
    balance = models.DecimalField(default=0, max_digits=14, decimal_places=2)
    
    def __str__(self) -> str:
        return str(self.account_number)
    

class UserAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="address")
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_code = models.IntegerField()
    country = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return self.user.email