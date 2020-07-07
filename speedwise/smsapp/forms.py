from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *


class ClientForm(forms.ModelForm):
    class Meta:
        model=Client
        fields=['user','mobile','logo','operator','credit_in','credit_out','is_active','create_date']


class UsercreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2','first_name','last_name']


class OperatorForm(forms.ModelForm):
    class Meta:
        model=Operator
        fields=['name','code','token','operator_number','create_date','is_active']


class ContactForm(forms.ModelForm):
    class Meta:
        model=Contact
        fields=['name','mobile','client','is_active','create_date']

class MessagesForm(forms.ModelForm):
    class Meta:
        model=Messages
        fields=['client','contact','message_out','message_reply','create_date','reply_date']