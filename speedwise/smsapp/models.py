from django.db import models
from datetime import date,datetime
from django.contrib.auth.models import User

# Create your models here.

class Operator(models.Model):
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=500)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Client(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    mobile = models.CharField(max_length=20,blank=True, null=True)
    logo = models.FileField(upload_to='media/logos',blank=True, null=True)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, null=True, blank=True)
    credit_in = models.FloatField(null=True, blank=True, default=0.0)
    credit_out = models.FloatField(null=True, blank=True, default=0.0)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.first_name
