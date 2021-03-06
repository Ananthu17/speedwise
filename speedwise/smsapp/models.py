from django.db import models
from datetime import date,datetime
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

# Create your models here.

class Operator(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3,validators=[MinLengthValidator(3)],default="NIL")
    account_id = models.CharField(max_length=100,blank=True, null=True)
    username = models.CharField(max_length=100,blank=True, null=True)
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


class Color(models.Model):
    color=models.CharField(max_length=20,blank=True, null=True)

    def __str__(self):
        return self.color

class Client(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,blank=True, null=True)
    mobile = models.CharField(max_length=20,blank=True, null=True)
    country = models.ForeignKey(Country,related_name='related_country',on_delete=models.CASCADE, null=True, blank=True)
    logo = models.FileField(upload_to='media/logos',blank=True, null=True)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, null=True, blank=True)
    credit = models.FloatField(null=True, blank=True, default=0.0)
    credit_limit = models.FloatField(null=True, blank=True, default=0.0)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    countries = models.ManyToManyField(Country,related_name='related_countries')
    color = models.ForeignKey(Color,related_name='related_color',on_delete=models.CASCADE , blank=True, null=True)


    def __str__(self):
        return self.user.username

class ClientSubUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True,blank=True)
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.user.username

class ClientCreditInOuts(models.Model):
    amount = models.FloatField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    is_credit = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.amount

class AuthInformation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.user.username

class ContactGroup(models.Model):
    name=models.CharField(max_length=100,blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name


class Contact(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(ContactGroup, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
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
    is_inbound = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.message

class MMSMessages(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    template = models.ForeignKey(Templates, on_delete=models.CASCADE, null=True, blank=True)
    attachment = models.FileField(upload_to='media/mmsattachments', blank=True, null=True)
    message_subject = models.TextField(blank=True, null=True)
    is_inbound = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.message


class Notifications(models.Model):
    message_out = models.TextField(blank=True, null=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    notification =  models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.notification

class ActionLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)
    action = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.action

class WebhookResponse(models.Model):
    message_response = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.message_response