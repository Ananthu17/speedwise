from django.db import models
from datetime import date,datetime
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

# Create your models here.

class Operator(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3,validators=[MinLengthValidator(3)],default="NIL")
    token = models.CharField(max_length=500)
    operator_number = models.CharField(max_length=500)
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
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.user.first_name

class Contact(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Messages(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    message_out = models.TextField(blank=True, null=True)
    message_reply = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    reply_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.message_out

