from django.db import models
from datetime import date,datetime
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

# Create your models here.

class Operator(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3,validators=[MinLengthValidator(3)],default="NIL")
    token = models.CharField(max_length=500)
    operator_number = models.CharField(max_length=500,blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Country(models.Model):
    country_name = models.CharField(max_length=100, blank=True, null=True)
    country_code = models.CharField(max_length=5, blank=True, null=True)
    country_tele_code = models.CharField(max_length=8, blank=True, null=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.country_name

class Client(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,blank=True, null=True)
    mobile = models.CharField(max_length=20,blank=True, null=True)
    logo = models.FileField(upload_to='media/logos',blank=True, null=True)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, null=True, blank=True)
    credit_in = models.FloatField(null=True, blank=True, default=0.0)
    credit_out = models.FloatField(null=True, blank=True, default=0.0)
    credit_limit = models.FloatField(null=True, blank=True, default=0.0)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    countries = models.ManyToManyField(Country)

    def __str__(self):
        return self.user.username

class ClientSubUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.user.username

class Contact(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

class Templates(models.Model):
    message_title = models.CharField(max_length=100, blank=True, null=True)
    message_template =  models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.message_title


class Messages(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    template = models.ForeignKey(Templates, on_delete=models.CASCADE, null=True, blank=True)
    message_telnyx_id = models.CharField(max_length=150, blank=True, null=True)
    message_out = models.TextField(blank=True, null=True)
    message_reply = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    reply_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.message_out


