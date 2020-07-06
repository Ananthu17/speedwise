from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *


class ClientForm(forms.ModelForm):
    class Meta:
        model=Client
        fields=['mobile','logo','operator','credit_in','credit_out','is_active']


class UsercreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2','first_name','last_name']


class OperatorForm(forms.ModelForm):
    class Meta:
        model=Operator
        fields=['name','token','create_date','is_active']
