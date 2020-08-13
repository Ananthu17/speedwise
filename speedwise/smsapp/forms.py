from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *


class ClientForm(forms.ModelForm):
    class Meta:
        model=Client
        fields=['mobile','logo','operator','credit_in','credit_out','credit_limit','is_active','create_date','country','color']
        widgets={
            'mobile':forms.TextInput(attrs={'class': 'form-control','placeholder':'Mobile Number'}),
            'logo':forms.FileInput(attrs={'class':"custom-file-input","id":"customFile"}),
            'operator':forms.Select(attrs={'class': 'form-control'}),
            'credit_in':forms.NumberInput(attrs={'class': 'form-control','placeholder':'0.0'}),
            'credit_out':forms.NumberInput(attrs={'class': 'form-control','placeholder':'0.0'}),
            'credit_limit':forms.NumberInput(attrs={'class': 'form-control','placeholder':'0.0'}),
            'is_active':forms.CheckboxInput(attrs={'class':'mt-1'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-control'}),
        }

class UsercreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2','first_name','last_name','email']
        widgets={
            'email':forms.TextInput(attrs={'class': 'form-control','placeholder':'Email'}),
            'username':forms.TextInput(attrs={'class': 'form-control','placeholder':'User Name'}),
            'password1':forms.TextInput(attrs={'class': 'form-control'}),
            'password2':forms.TextInput(attrs={'class': 'form-control'}),
            'first_name':forms.TextInput(attrs={'class': 'form-control','placeholder':'First Name'}),
            'last_name':forms.TextInput(attrs={'class': 'form-control','placeholder':'Last Name'}),
        }


class ClientSubUserForm(forms.ModelForm):
    class Meta:
        model=ClientSubUser
        fields=['mobile','country','is_active','create_date']
        widgets={
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'is_active':forms.CheckboxInput(attrs={'class':'mt-1 pt-2'}),
            'create_date':forms.DateInput(attrs={'class': 'form-control'}),
        }

class OperatorForm(forms.ModelForm):
    class Meta:
        model=Operator
        fields=['name','code','username','account_id','token','operator_number','create_date','is_active']
        widgets={
            'name':forms.TextInput(attrs={'class': 'form-control','placeholder':'Name'}),
            'username':forms.TextInput(attrs={'class': 'form-control','placeholder':'Username'}),
            'account_id':forms.TextInput(attrs={'class': 'form-control','placeholder':'AccountID'}),
            'code':forms.TextInput(attrs={'class': 'form-control','placeholder':'Code'}),
            'token':forms.TextInput(attrs={'class': 'form-control','placeholder':'Token'}),
            'operator_number':forms.TextInput(attrs={'class': 'form-control','placeholder':'Number'}),
            'create_date':forms.TextInput(attrs={'class': 'form-control'}),
            'is_active':forms.CheckboxInput(attrs={'class':'ml-1 mt-2'}),
        }

class ContactGroupForm(forms.ModelForm):
    class Meta:
        model=ContactGroup
        fields=['name','client','user','is_active','create_date']

class ContactForm(forms.ModelForm):
    class Meta:
        model=Contact
        fields=['name','mobile','user','group','country','is_active','create_date']
        widgets = {
            'name':forms.TextInput(attrs={'class': 'form-control','placeholder':'Name'}),
            'mobile':forms.TextInput(attrs={'class': 'form-control','placeholder':'Mobile'}),
            # 'client':forms.Select(attrs={'class': 'form-control'}),
            'country':forms.Select(attrs={'class': 'form-control',}),
            'create_date':forms.TextInput(attrs={'class': 'form-control','placeholder':''}),
        }

class MessagesForm(forms.ModelForm):
    class Meta:
        model=Messages
        fields=['client','user','contact','template','message','create_date']
        widgets={
            'template': forms.Select(attrs={'class': 'form-control mb-1'}),
            'client':forms.Select(attrs={'class': 'form-control mb-1'}),
            'user':forms.Select(attrs={'class': 'form-control mb-1'}),
            'message':forms.Textarea(attrs={'class': 'form-control mb-1','placeholder':'Enter Your Messages..'})
        }

class MMSMessagesForm(forms.ModelForm):
    class Meta:
        model=MMSMessages
        fields=['client','user','contact','template','attachment','message_subject','message','create_date']
        widgets ={
            'client':forms.Select(attrs={'class': 'form-control mb-1'}),
            'user':forms.Select(attrs={'class': 'form-control mb-1'}),
            'template': forms.Select(attrs={'class': 'form-control mb-1'}),
            'attachment':forms.FileInput(attrs={'class':"custom-file-input","id":"customFile"}),
            'message_subject':forms.Textarea(attrs={'class': 'form-control mb-1','placeholder':'Enter Your Messages..'}),
            'message':forms.Textarea(attrs={'class': 'form-control mb-1','placeholder':'Enter Your Messages..'})
        }

class TemplateForm(forms.ModelForm):
    class Meta:
        model = Templates
        fields = ['message_title', 'message_template', 'created_by', 'create_date']
        widgets={
            'message_title': forms.TextInput(attrs={'class': 'form-control'}),
            'message_template':forms.Textarea(attrs={'class': 'form-control','placeholder':'Enter Your Messages..'}),
            'created_by':forms.Select(attrs={'class': 'form-control'}),
            'create_date':forms.DateInput(attrs={'class': 'form-control'})
        }

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['country_name', 'country_code', 'country_tele_code']
        widgets={
            'country_name': forms.TextInput(attrs={'class': 'form-control','placeholder':'Country Name'}),
            'country_code': forms.TextInput(attrs={'class': 'form-control','placeholder':'Country Code'}),
            'country_tele_code': forms.TextInput(attrs={'class': 'form-control','placeholder':'Tele Code'}),
        }
