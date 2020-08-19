from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from .models import *
import pandas as pd
import json
import datetime
from datetime import timedelta
import dateutil.relativedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login,logout
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
import telnyx
import base64
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from authy.api import AuthyApiClient
import pyotp




class DashboardView(TemplateView):
    template_name = 'smsapp/index.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['client'] = Client.objects.all()
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        else:
            context = super(DashboardView, self).dispatch(request, *args, **kwargs)
        return context

class ClientView(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/clients.html'
    login_url = 'login'


    def get_context_data(self, **kwargs):
        context = super(ClientView, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            if Client.objects.filter(user=self.request.user):
                logged_client = Client.objects.get(user=self.request.user)
                context['logged_client'] = logged_client
            if ClientSubUser.objects.filter(user=self.request.user):
                logged_client = ClientSubUser.objects.get(user=self.request.user).client
                context['logged_client'] = logged_client
            client_objects = Client.objects.all()
            operators = Operator.objects.all()
            countries = Country.objects.all()
            clientform = ClientForm
            userform = UsercreateForm
            context['clients'] = client_objects
            context['clientform'] = clientform
            context['userform'] = userform
            context['operators'] = operators
            context['countries'] = countries

        else:
            messages.info(self.request, "You are not authourized to access this records")
        return context

    def post(self,request):
        try:
            if not User.objects.filter(id=request.POST.get('user')):
                clientform = ClientForm(request.POST, request.FILES or None)
                userform = UsercreateForm(request.POST or None)
                if userform.is_valid() and clientform.is_valid():
                    user = userform.save()
                    user.is_staff = False
                    user.save()
                    client = clientform.save()
                    client.user = user
                    try:
                        permitted_countries = request.POST.getlist('countries', '')
                        for country_id in permitted_countries:
                            country = Country.objects.get(id=country_id)
                            client.countries.add(country)
                    except:
                        None
                    client.save()
                return redirect('clients')

            else:
                user = User.objects.get(id=request.POST.get('user'))
                client = Client.objects.get(user=user)
                client.mobile = request.POST.get('mobile', '')
                client.user.email = request.POST.get('email', '')
                client.user.save()
                client.logo = request.FILES.get('logo', '')
                try:
                    client.operator = Operator.objects.get(id=request.POST.get('operator',''))
                except:
                    None
                try:
                    client.country = Country.objects.get(id=request.POST.get('own_country',''))
                except:
                    None
                client.credit = request.POST.get('credin', '')
                client.credit_limit = request.POST.get('credlimit', '')
                client.is_active = True if request.POST.get('active_status', '') == 'on' else False
                try:
                    permitted_countries = request.POST.get('countries', '')
                    for country_id in permitted_countries:
                        country=Country.objects.get(id=country_id)
                        client.countries.add(country)
                except:
                    None
                client.save()
                return redirect('clients')

        except:
            messages.error(request,"Something went wrong")
            return redirect('clients')

def delete_user(request, user_pk):
    try:
        user = Client.objects.get(pk=user_pk).user
        user.delete()
        action = str(request.user) + ' deleted ' + str(user) + ' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ActionLogs.objects.create(user=request.user, action=action)
        return redirect('clients')
    except:
        messages.error(request, "Something went wrong")
        return redirect('clients')

class ClientSubUserView(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/client_profile.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(ClientSubUserView, self).get_context_data(**kwargs)
        return context


    def post(self,request):
        try:
            clientsubuserform = ClientSubUserForm(request.POST, request.FILES or None)
            userform = UsercreateForm(request.POST or None)
            if userform.is_valid() and clientsubuserform.is_valid():
                user = userform.save()
                user.is_staff = False
                user.save()
                client = Client.objects.get(id=request.POST.get('client'))
                clientsubuser = clientsubuserform.save()
                clientsubuser.user = user
                clientsubuser.client = client
                clientsubuser.save()
                action = str(request.user) + ' created ' +str(clientsubuser)+' at '+ datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
            return redirect('clientprofile',client.id)
        except:
            messages.error(request,"Something went wrong")
            return redirect('clients')



class LoginView(TemplateView):
    template_name = 'smsapp/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('index'))
        else:
            context = super(LoginView, self).dispatch(request, *args, **kwargs)
        return context

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        return context

    def post(self, request):
        try:
            email = request.POST.get('email', '')
            print(email)
            password = request.POST.get('password', '')
            username = User.objects.get(email=email.lower()).username
            if username and password:
                user = authenticate(username=username, password=password)
                if user is not None:
                    if user.is_superuser:
                        try:
                            user_2fa = AuthInformation.objects.filter(user=user)
                            if user_2fa:
                                user_2fa = AuthInformation.objects.get(user=user)
                                if user_2fa.is_active:
                                    secret_key = user_2fa.secret_key
                                    return render(request, 'smsapp/verify-2fa-token.html',{'secret_key': secret_key, 'user': user.id})
                                else:
                                    messages.error(request, "TFA not active")
                                    return redirect('login')
                            else:
                                login(request, user)
                                action = str(user) +' logged in at '+datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                ActionLogs.objects.create(user=user,action=action)
                                return redirect('index')
                        except:
                            messages.error(request, "Something went wrong with the connection")
                            return redirect('login')

                    else:
                        if ClientSubUser.objects.filter(user = user):
                            if ClientSubUser.objects.get(user = user).is_active:
                                try:
                                    user_2fa = AuthInformation.objects.filter(user=user)
                                    if user_2fa:
                                        user_2fa = AuthInformation.objects.get(user=user)
                                        if user_2fa.is_active:
                                            secret_key = user_2fa.secret_key
                                            return render(request, 'smsapp/verify-2fa-token.html',{'secret_key': secret_key, 'user': user.id})
                                        else:
                                            messages.error(request, "TFA not active")
                                            return redirect('login')
                                    else:
                                        login(request, user)
                                        action = str(user) + ' logged in at ' + datetime.now().strftime(
                                            "%d/%m/%Y %H:%M:%S")
                                        ActionLogs.objects.create(user=user, action=action)
                                        return redirect('messaging')
                                except:
                                    messages.error(request, "Something went wrong with the connection")
                                    return redirect('login')
                            else:
                                messages.error(request,"Contact administrator to activate the account")
                                return redirect('login')
                        else:
                            if Client.objects.filter(user = user):
                                if Client.objects.get(user = user).is_active:
                                    try:
                                        user_2fa = AuthInformation.objects.filter(user=user)
                                        if user_2fa:
                                            user_2fa = AuthInformation.objects.get(user=user)
                                            if user_2fa.is_active:
                                                secret_key = user_2fa.secret_key
                                                return render(request, 'smsapp/verify-2fa-token.html',{'secret_key': secret_key, 'user': user.id})
                                            else:
                                                messages.error(request, "TFA not active")
                                                return redirect('login')
                                        else:
                                            login(request, user)
                                            action = str(user) + ' logged in at ' + datetime.now().strftime(
                                                "%d/%m/%Y %H:%M:%S")
                                            ActionLogs.objects.create(user=user, action=action)
                                            return redirect('index')
                                    except:
                                        messages.error(request, "Something went wrong with the connection")
                                        return redirect('login')
                                else:
                                    messages.error(request,"Contact administrator to activate the account")
                                    return redirect('login')
                else:
                    messages.error(request,
                                   "Invalid Credentials")
                    return redirect('login')
            else:
                messages.error(request,
                               "Username or password are required")
                return redirect('login')
        except:
            messages.error(request,
                           "Invalid Credentials")
            return redirect('login')


def enable_2fa(request):
    if request.method=='GET':

        user_exist = AuthInformation.objects.filter(user=request.user)
        if user_exist:
            user_2fa = AuthInformation.objects.get(user=request.user)
            if user_2fa.is_active:
                secret_url = 'otpauth://totp/Speedwise%20App:speedwise%40google.com?secret=' + str(user_2fa.secret_key) + '&issuer=Speedwise%20App'
                return render(request, 'smsapp/enable_2fa.html',{'secret_key': user_2fa.secret_key, 'user': request.user.id ,'secret_url':secret_url})
            else:
                return render(request, 'smsapp/enable_2fa.html')
        else:
            return render(request, 'smsapp/enable_2fa.html')
    if request.method == 'POST':
        if request.POST.get('disable_2fa'):
            user_2fa = AuthInformation.objects.filter(user=request.user)
            if user_2fa:
                user_2fa = AuthInformation.objects.get(user=request.user)
                return render(request, 'smsapp/verify-2fa-token.html',{'disable_secret_key': user_2fa.secret_key,'user': request.user.id})
        else:
            user_2fa = AuthInformation.objects.filter(user=request.user)
            if not user_2fa:
                AuthInformation.objects.create(user=request.user,is_active=True,secret_key=pyotp.random_base32())
                action = str(request.user) + ' enabled two factor authentication at ' + datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
            return redirect('enable-2fa')

def verify_2fa_token(request):
    try:
        if request.POST.get('secret_key'):
            user = User.objects.get(id=request.POST.get('user'))
            secret_key=request.POST.get('secret_key')
            totp = pyotp.TOTP(secret_key)
            verify = totp.verify(request.POST.get('token'))
            if verify == True:
                login(request, user)
                ActionLogs.objects.create(user=user, action="enabled two factor authentication")
                return redirect('index')
            else:
                messages.error(request, "Token Invalid")
                return redirect('login')
        if request.POST.get('disable_secret_key'):
            user = User.objects.get(id=request.POST.get('user'))
            secret_key = request.POST.get('disable_secret_key')
            totp = pyotp.TOTP(secret_key)
            verify = totp.verify(request.POST.get('token'))
            if verify == True:
                user_2fa = AuthInformation.objects.get(user=request.user)
                user_2fa.delete()
                action = str(user) + ' disabled two factor authentication at ' + datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=user, action=action)
                return redirect('index')
            else:
                return redirect('login')
    except:
        return redirect('login')


class RegisterView(TemplateView):
    template_name = 'smsapp/register.html'

    def get_context_data(self, **kwargs):
        context = super(RegisterView, self).get_context_data(**kwargs)
        return context

    def post(self,request):
        try:
            if request.method == 'POST':
                first_name =request.POST['first_name']
                last_name =request.POST['last_name']
                mobile =request.POST['mobile']
                email =request.POST['email']
                username =request.POST['username']
                password1 =request.POST['password1']
                password2 =request.POST['password2']
                logo =request.FILES['logo']
                print(logo)
                if password1 == password2:
                    if User.objects.filter(username=username).exists():
                        messages.info(request,'User already exists')
                        return render(request, 'smsapp/register.html')
                    elif User.objects.filter(email=email).exists():
                        messages.info(request, 'Email already taken')
                        return render(request, 'smsapp/register.html')
                    else:
                        user = User.objects.create_user(username=username,password=password1,first_name=first_name,last_name=last_name,email=email)
                        user.save()
                        client = Client.objects.create(user=user,mobile=mobile,logo=logo)
                        client.save()
                        return redirect(reverse('login'))
                else:
                    messages.info(request,'password not matching')
                    return render(request, 'smsapp/register.html')
            else:
                return render(request,'smsapp/register.html')
        except:
            messages.error(request, "Something went wrong")
            return render(request,'smsapp/register.html')


def logout_view(request):
    if request.user.is_authenticated:
        action = str(request.user) + ' logged out at ' + datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S")
        ActionLogs.objects.create(user=request.user, action=action)
        logout(request)
    return redirect(reverse('login'))

class ClientProfile(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/client_profile.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(ClientProfile, self).get_context_data(**kwargs)
        client_object = Client.objects.get(pk=kwargs['user_pk'])
        countries= Country.objects.all()
        operators = Operator.objects.all()
        action_logs = ActionLogs.objects.all()
        credit_objects = ClientCreditInOuts.objects.filter(is_credit=True)
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        if self.request.user.is_superuser:
            client_sub_user_objects = ClientSubUser.objects.all()
            userform = UsercreateForm
            clientsubuserform = ClientSubUserForm
            context['clientsubusers'] = client_sub_user_objects
            context['clientsubuserform'] = clientsubuserform
            context['userform'] = userform
            context['operators'] = operators
            context['action_logs'] = action_logs
            context['credit_objects'] = credit_objects
            notifications = Notifications.objects.all()
            context['notifications'] = notifications

        else:
            client_sub_user_objects = ClientSubUser.objects.filter(client=Client.objects.get(user=self.request.user))
            userform = UsercreateForm
            clientsubuserform = ClientSubUserForm
            context['clientsubusers'] = client_sub_user_objects
            context['clientsubuserform'] = clientsubuserform
            context['userform'] = userform
            context['operators'] = operators
            context['action_logs'] = action_logs
            context['credit_objects'] = credit_objects

        context['client'] = client_object
        print(client_object.countries.all())
        context['countries']= countries
        return context

    def post(self,request,user_pk):
        if request.method == "POST":
            client = Client.objects.get(id=user_pk)
            allowed_countries = request.POST.getlist('states[]')
            if allowed_countries:
                client.countries.clear()
                try:
                    for country in allowed_countries:
                        country_object = Country.objects.get(pk=country)
                        client.countries.add(country_object)
                        client.save()
                    return redirect('clientprofile', client.id)
                except:
                    messages.error(request, "Something went wrong")
                    return redirect('clientprofile', client.id)
        return redirect('clientprofile',client.id)


def add_client_credit(request,user_pk):
    try:
        client_object = Client.objects.get(pk=user_pk)
        credit_amount = request.POST.get('credit')
        credit_obj = ClientCreditInOuts.objects.create(amount=float(credit_amount),client=client_object,is_credit=True)
        client_object.credit+=float(credit_amount)
        client_object.save()
        return redirect('clientprofile',user_pk)
    except:
        messages.error(request, "Something went wrong")
        return redirect('clientprofile', user_pk)

def remove_client_credit(request,user_pk):
    try:
        client_object = Client.objects.get(pk=user_pk)
        remove_amount = request.POST.get('removecredit')
        if ClientCreditInOuts.objects.filter(id=request.POST.get('credit_id')):
            credit_obj = ClientCreditInOuts.objects.get(id=request.POST.get('credit_id'))
            credit_obj.delete()
        client_object.credit-=float(remove_amount)
        client_object.save()
        return redirect('clientprofile',user_pk)
    except:
        messages.error(request, "Something went wrong")
        return redirect('clientprofile', user_pk)

def set_client_credit_limit(request,user_pk):
    try:
        client_object = Client.objects.get(pk=user_pk)
        credit_limit = request.POST.get('credit_limit')
        client_object.credit_limit=float(credit_limit)
        client_object.save()
        return redirect('clientprofile',user_pk)
    except:
        messages.error(request, "Something went wrong")
        return redirect('clientprofile', user_pk)

def change_client_logo(request,user_pk):
    try:
        client_object = Client.objects.get(pk=user_pk)
        logo = request.FILES['logo']
        client_object.logo = logo
        client_object.save()
        return redirect('clientprofile',user_pk)
    except:
        messages.error(request, "Something went wrong")
        return redirect('clientprofile', user_pk)

def allowed_countries_for_clients(request,user_pk):
    client = Client.objects.get(pk=user_pk)
    if request.method == "POST":
        allowed_countries = request.POST.getlist('states[]')
        print(allowed_countries)
        if allowed_countries:
            client.countries.clear()
            try:
                for country in allowed_countries:
                    country_object = Country.objects.get(pk=country)
                    client.countries.add(country_object)
                    client.save()
                return redirect('clientprofile', user_pk)
            except:
                messages.error(request, "Something went wrong")
                return redirect('clientprofile', user_pk)
        else:
            return redirect('clientprofile', user_pk)
    else:
        return redirect('clientprofile', user_pk)



class Operators(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/operators.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Operators, self).get_context_data(**kwargs)
        operatorform = OperatorForm
        context['operatorform'] = operatorform
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
            notifications = Notifications.objects.filter(client=logged_client)
            context['notifications'] = notifications
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
            notifications = Notifications.objects.filter(client=logged_client)
            context['notifications'] = notifications
        if self.request.user.is_superuser:
            operators = Operator.objects.all()
            context['operators'] = operators
            context['notifications'] = Notifications.objects.all()
        return context

    def post(self,request):
        try:
            if Operator.objects.filter(id=request.POST.get('operator_id')):
                print(request.POST)
                operator = Operator.objects.get(id=request.POST.get('operator_id'))
                operator.name = request.POST.get('name')
                operator.username = request.POST.get('username')
                operator.account_id = request.POST.get('account_id')
                operator.code = request.POST.get('code')
                operator.token = request.POST.get('token')
                operator.operator_number = request.POST.get('number')
                operator.save()
                return redirect('operators')
            elif request.POST.get('action_type') == 'enable_operator':
                print(request.POST.get('id'),request.POST.get('is_active'))
                operator = Operator.objects.get(id=request.POST.get('id'))
                operator.is_active = request.POST.get('is_active') == 'true'
                operator.save()
                print(operator.is_active)
                return redirect('operators')
            else:
                operatorform = OperatorForm(request.POST,request.FILES or None)
                if operatorform.is_valid():
                    operator = operatorform.save()
                    operator.save()
                return redirect('operators')
        except:
            messages.error(request,"Something went wrong")
            return redirect('operators')


def delete_operator(request, operator_pk):
    try:
        operator = Operator.objects.get(pk=operator_pk)
        operator.delete()
        return redirect('operators')
    except:
        messages.error(request, "Something went wrong")
        return redirect('operators')


class Contacts_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/contacts.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Contacts_View, self).get_context_data(**kwargs)
        contactform = ContactForm
        user=self.request.user
        if user.is_authenticated:
            if Client.objects.filter(user=self.request.user):
                logged_client = Client.objects.get(user=self.request.user)
                context['logged_client'] = logged_client
            if ClientSubUser.objects.filter(user=self.request.user):
                logged_client = ClientSubUser.objects.get(user=self.request.user).client
                context['logged_client'] = logged_client

            if self.request.user.is_superuser:
                countries = Country.objects.all()
                contacts = Contact.objects.all()
                clients = Client.objects.all()
                notifications = Notifications.objects.all()
                context['notifications'] = notifications
                context['contactsform'] = contactform
                context['contacts'] = contacts
                context['countries'] = countries
                context['clients'] = clients

            else:
                if Client.objects.filter(user=self.request.user):
                    client = Client.objects.get(user=self.request.user)
                if ClientSubUser.objects.filter(user=self.request.user):
                    client = ClientSubUser.objects.get(user=self.request.user).client
                countries = client.countries.all()
                contacts = Contact.objects.filter(client=client)
                notifications = Notifications.objects.filter(client=client)
                context['notifications'] = notifications
                context['contactsform'] = contactform
                context['contacts'] = contacts
                context['countries'] = countries
        else:
            pass
        
        return context

    def post(self, request):
        try:
            if Contact.objects.filter(id=request.POST.get('contact_id')):
                contact = Contact.objects.get(id=request.POST.get('contact_id'))
                contact.name = request.POST.get('name')
                contact.mobile = request.POST.get('mobile')
                contact.country = Country.objects.get(pk=request.POST.get('country'))
                contact.user = self.request.user
                contact.save()
                action = str(self.request.user) + ' updated '+str(contact)+' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
                return redirect('contacts')
            elif request.POST.get('action_type') == 'enable_contact':
                contact = Contact.objects.get(id=request.POST.get('id'))
                contact.is_active = request.POST.get('is_active') == 'true'
                contact.save()
                action = str(self.request.user) + ' enabled/disabled '+str(contact)+' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
                return redirect('contacts')
            else:
                contactsform = ContactForm(request.POST, request.FILES or None)
                if contactsform.is_valid():
                    contacts = contactsform.save()
                    if self.request.user.is_superuser:
                        client = Client.objects.get(pk=request.POST.get('client'))
                        contacts.client = client
                    if Client.objects.filter(user=self.request.user):
                        client = Client.objects.get(user=self.request.user)
                        contacts.client=client
                    if ClientSubUser.objects.filter(user=self.request.user):
                        client = ClientSubUser.objects.get(user=self.request.user).client
                        contacts.client = client
                    mobile = [character for character in str(contacts.mobile) if character.isalnum()]
                    contacts.mobile = "".join(mobile)
                    contacts.country = Country.objects.get(pk=request.POST.get('country_filtered'))
                    contacts.user=self.request.user
                    contacts.save()
                    action = str(self.request.user) + ' created contact ' + str(contacts) + ' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    ActionLogs.objects.create(user=request.user, action=action)
                return redirect('contacts')
        except:
            messages.error(request, "Something went wrong")
            return redirect('contacts')


def import_contacts(request):
    try:
        if request.method == 'POST' and request.FILES['file_upload']:
            file = request.FILES['file_upload']
            file_format = str(file).split('.')[-1]
            if file_format == 'csv':
                data = pd.read_csv(file)
            else:
                messages.error(request, "Please use a CSV file to import")
                return redirect('contacts')

            for i,j in data.iterrows():

                if Client.objects.filter(user=request.user):
                    client = Client.objects.get(user=request.user)
                    user = request.user
                    country = Country.objects.get(country_code=j[2])
                    group = ContactGroup.objects.get(name=j[3]) or None
                    mobile = [character for character in str(j[1]) if character.isalnum()]
                    mobile = "".join(mobile)
                    if not Contact.objects.filter(name=j[0], mobile=mobile):
                        contact = Contact.objects.create(name=j[0], mobile=mobile, client=client, user=user,
                                                         country=country,group=group)
                        contact.save()
                elif ClientSubUser.objects.filter(user=request.user):
                    client = ClientSubUser.objects.get(user=request.user).client
                    user = request.user
                    country = Country.objects.get(country_code=j[2])
                    group = ContactGroup.objects.get(name=j[3]) or None
                    mobile = [character for character in str(j[1]) if character.isalnum()]
                    mobile = "".join(mobile)
                    if not Contact.objects.filter(name=j[0], mobile=mobile):
                        contact = Contact.objects.create(name=j[0], mobile=mobile, client=client, user=user,
                                                         country=country,group=group)
                        contact.save()
                else:
                    user = request.user
                    country = Country.objects.get(country_code=j[2])
                    group = ContactGroup.objects.get(name=j[3]) or None
                    mobile = [character for character in str(j[1]) if character.isalnum()]
                    mobile = "".join(mobile)
                    if not Contact.objects.filter(name=j[0], mobile=mobile):
                        contact = Contact.objects.create(name=j[0], mobile=mobile, user=user,country=country,group=group)
                        contact.save()
            action = str(request.user) + ' imported contacts at ' + datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S")
            ActionLogs.objects.create(user=request.user, action=action)
            return redirect('contacts')

    except:
        messages.error(request, "Something went wrong")
        return redirect('contacts')

def delete_contact(request, contact_pk):
    try:
        contact = Contact.objects.get(pk=contact_pk)
        contact.delete()
        action = str(request.user) + ' deleted a contact '+str(contact)+' at ' + datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S")
        ActionLogs.objects.create(user=request.user, action=action)
        return redirect('contacts')
    except:
        messages.error(request, "Something went wrong")
        return redirect('contacts')

class ContactsGroup_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/contacts_group.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(ContactsGroup_View, self).get_context_data(**kwargs)
        contactgroupform = ContactGroupForm
        user = self.request.user
        if user.is_authenticated:
            if Client.objects.filter(user=self.request.user):
                logged_client = Client.objects.get(user=self.request.user)
                context['logged_client'] = logged_client
            if ClientSubUser.objects.filter(user=self.request.user):
                logged_client = ClientSubUser.objects.get(user=self.request.user).client
                context['logged_client'] = logged_client
            if self.request.user.is_superuser:
                contact_groups = ContactGroup.objects.all()
                clients = Client.objects.all()
                notifications = Notifications.objects.all()
                context['notifications'] = notifications
                context['contactgroupform'] = contactgroupform
                context['clients'] = clients
                context['contact_groups'] = contact_groups
            else:
                if Client.objects.filter(user=self.request.user):
                    client = Client.objects.get(user=self.request.user)
                if ClientSubUser.objects.filter(user=self.request.user):
                    client = ClientSubUser.objects.get(user=self.request.user).client
                notifications = Notifications.objects.filter(client=client)
                context['notifications'] = notifications
                contact_groups = ContactGroup.objects.filter(client=client)
                context['contactgroupform'] = contactgroupform
                context['contact_groups'] = contact_groups
        else:
            pass
        return context

    def post(self, request):
        try:
            if ContactGroup.objects.filter(id=request.POST.get('contact_group_id')):
                contact_group = ContactGroup.objects.get(id=request.POST.get('contact_group_id'))
                contact_group.name = request.POST.get('name')
                contact_group.user = self.request.user
                contact_group.save()
                action = str(self.request.user) + ' updated '+str(contact_group)+' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
                return redirect('contacts-groups')
            elif request.POST.get('action_type') == 'enable_contact_group':
                contact_group = ContactGroup.objects.get(id=request.POST.get('id'))
                contact_group.is_active = request.POST.get('is_active') == 'true'
                contact_group.save()
                action = str(self.request.user) + ' enabled/disabled '+str(contact_group)+' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
                return redirect('contacts-groups')
            else:
                contactgroupform = ContactGroupForm(request.POST, request.FILES or None)
                if contactgroupform.is_valid():
                    contact_group = contactgroupform.save()
                    if self.request.user.is_superuser:
                        client = Client.objects.get(pk=request.POST.get('client'))
                        contact_group.client = client
                    if Client.objects.filter(user=self.request.user):
                        client = Client.objects.get(user=self.request.user)
                        contact_group.client=client
                    if ClientSubUser.objects.filter(user=self.request.user):
                        client = ClientSubUser.objects.get(user=self.request.user).client
                        contact_group.client = client
                    contact_group.user = self.request.user
                    contact_group.save()
                    action = str(self.request.user) + ' created contact ' + str(contact_group) + ' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    ActionLogs.objects.create(user=request.user, action=action)
                return redirect('contacts-groups')
        except:
            messages.error(request, "Something went wrong")
            return redirect('contacts-groups')


class Messages_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/messages.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Messages_View, self).get_context_data(**kwargs)
        messagingform = MessagesForm
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        if self.request.user.is_superuser:
            messages = Messages.objects.all()
            contacts = Contact.objects.all()
            notifications = Notifications.objects.all()
            context['notifications'] = notifications
        else:
            if Client.objects.filter(user=self.request.user):
                client = Client.objects.get(user=self.request.user)
                contacts = Contact.objects.filter(client=client)
                notifications = Notifications.objects.filter(client=client)
                context['notifications'] = notifications
            else:
                client = ClientSubUser.objects.get(user=self.request.user).client
                contacts = Contact.objects.filter(client=client)
                notifications = Notifications.objects.filter(client=client)
                context['notifications'] = notifications
            messages = Messages.objects.filter(client=client)
        contacts_gp = ContactGroup.objects.all()

        templates = Templates.objects.all()
        context['messagingform'] = messagingform
        context['messageslist'] = messages
        context['contacts'] = contacts
        context['contacts_group'] = contacts_gp
        threads = []
        for contact in contacts:
            if Messages.objects.filter(contact=contact):
                thread = {
                    'contact': Contact.objects.get(id=contact.id),
                    'message': Messages.objects.filter(contact=contact)
                }
                threads.append(thread)
                context['messages_threads'] = threads
        context['templates'] = templates

        return context


    def post(self, request):
        try:
            contacts = request.POST.get('contactsList')
            contacts_groups = request.POST.get('contactsgroupList')
            destination_contacts = contacts.split(",")
            for group in contacts_groups.split(","):
                for contact in Contact.objects.filter(group=group):
                    destination_contacts.append(str(contact.id))
            msg = request.POST.get("message")
            print(msg)
            for item in destination_contacts:
                destination_contact = Contact.objects.get(id=item)
                country_tele_code = destination_contact.country.country_tele_code
                if self.request.user.is_superuser:
                    client = Client.objects.get(id=request.POST.get('client'))
                else:
                    if Client.objects.filter(user=self.request.user):
                        client = Client.objects.get(user=self.request.user)
                    else:
                        client = ClientSubUser.objects.get(user=self.request.user).client
                token = client.operator.token
                account_id = client.operator.account_id
                username = client.operator.username
                authentication = str(username)+":"+str(token)
                authentication_bytes = authentication.encode('ascii')
                authentication_bytes_base64 = base64.b64encode(authentication_bytes)
                authentication_bytes_base64_decode = authentication_bytes_base64.decode('ascii')
                source_number = client.operator.operator_number
                destination_contact_number = destination_contact.mobile
                no_country_perms=[]
                country_not_active=[]
                contact_not_active=[]
                if not destination_contact.is_active == False:
                    if not destination_contact.country.is_active == False:
                        if destination_contact.country in client.countries.all():
                            if client.credit_limit == client.credit:
                                messages.info(request, "You  have reached your credit limit. Kindly add credits.")
                                notification_entry = Notifications.objects.create(client=client,user=self.request.user,notification="You  have reached your credit limit. Kindly add credits.")
                                send_mail('Add your Credits', 'You have reached the credit limits', 'techspeedwise@gmail.com',[client.email], fail_silently=False)
                            if client.operator.code == 'TLX':
                                telnyx.api_key = token
                                send_msg = telnyx.Message.create(
                                    from_=source_number,
                                    to=country_tele_code+destination_contact_number,
                                    text=msg,
                                )
                                message_entry = Messages.objects.create(client=client,user=self.request.user,contact=destination_contact,message=msg)
                                credit_obj = ClientCreditInOuts.objects.create(amount=1.0,client=client)
                                client.credit-=1
                                client.save()
                            if client.operator.code == 'THQ':
                                url = "https://api.thinq.com/account/" + str(
                                    account_id) + "/product/origination/sms/send"
                                payload = "{\n  \"from_did\": \"" + source_number + "\",\n  \"to_did\": \"" +destination_contact_number+ "\",\n  \"message\": \"" + str(
                                    msg) + "\"\n}"
                                headers = {
                                    'Authorization': 'Basic ' + str(authentication_bytes_base64_decode),
                                    'Content-Type': 'application/json'
                                }
                                response = requests.request("POST", url, headers=headers, data=payload)
                                messages.info(request, response.text.encode('utf8'))
                                message_entry = Messages.objects.create(client=client, user=self.request.user,
                                                                        contact=destination_contact, message=msg)
                                credit_obj = ClientCreditInOuts.objects.create(amount=1.0, client=client)
                                client.credit-=1
                                client.save()
                        else:
                            no_country_perms.append(destination_contact)
                    else:
                        country_not_active.append(destination_contact)
                else:
                    contact_not_active.append(destination_contact)
            if no_country_perms:
                notification = str(len(no_country_perms))+' messages failed. Countries of the contacts are not permitted for the client.'
                notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,client=client,notification=notification)
            if country_not_active:
                notification = str(len(country_not_active)) + ' messages failed. Countries of the contacts are not active.'
                notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,client=client,notification=notification)
            if contact_not_active:
                notification = str(len(contact_not_active)) + ' messages failed. Contacts are not active.'
                notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,client=client,notification=notification)
            action = str(request.user) + ' sent some messages at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            ActionLogs.objects.create(user=request.user, action=action)
            return redirect('messaging')
        except:
            messages.error(request, "Something went wrong")
            return redirect('messaging')


def delete_message(request, message_pk):
    try:
        message = Messages.objects.get(pk=message_pk)
        message.delete()
        action = str(request.user) + ' deleted a message at ' + datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S")
        ActionLogs.objects.create(user=request.user, action=action)
        return redirect('messaging')
    except:
        messages.error(request, "Something went wrong")
        return redirect('messaging')


class MMSMessages_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/mmsmessages.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(MMSMessages_View, self).get_context_data(**kwargs)
        mmsmessagingform = MMSMessagesForm
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        if self.request.user.is_superuser:
            mmsmessages = MMSMessages.objects.all()
            contacts = Contact.objects.all()
            notifications = Notifications.objects.all()
            context['notifications'] = notifications
        else:
            if Client.objects.filter(user=self.request.user):
                client = Client.objects.get(user=self.request.user)
                contacts = Contact.objects.filter(client=client)
                notifications = Notifications.objects.filter(client=client)
                context['notifications'] = notifications
            else:
                client = ClientSubUser.objects.get(user=self.request.user).client
                contacts = Contact.objects.filter(client=client)
                notifications = Notifications.objects.filter(client=client)
                context['notifications'] = notifications
            mmsmessages = MMSMessages.objects.filter(client=client)
        templates = Templates.objects.all()
        context['mmsmessagingform'] = mmsmessagingform
        context['mmsmessageslist'] = mmsmessages
        context['contacts'] = contacts
        threads = []
        for contact in contacts:
            if MMSMessages.objects.filter(contact=contact):
                thread = {
                    'contact': Contact.objects.get(id=contact.id),
                    'message': MMSMessages.objects.filter(contact=contact)
                }
                threads.append(thread)
                context['messages_threads'] = threads
        contacts_gp = ContactGroup.objects.all()
        context['contacts_group'] = contacts_gp
        context['templates'] = templates
        return context

    def post(self, request):
        try:
            contacts = request.POST.get('contactsList')
            contacts_groups = request.POST.get('contactsgroupList')
            destination_contacts = contacts.split(",")
            for group in contacts_groups.split(","):
                for contact in Contact.objects.filter(group=group):
                    destination_contacts.append(str(contact.id))
            message_subject = request.POST.get("message_subject")
            msg = request.POST.get("message")
            for item in destination_contacts:
                destination_contact = Contact.objects.get(id=item)
                country_tele_code = destination_contact.country.country_tele_code
                if self.request.user.is_superuser:
                    client = Client.objects.get(id=request.POST.get('client'))
                else:
                    if Client.objects.filter(user=self.request.user):
                        client = Client.objects.get(user=self.request.user)
                    else:
                        client = ClientSubUser.objects.get(user=self.request.user).client
                token = client.operator.token
                account_id = client.operator.account_id
                username = client.operator.username
                authentication = str(username)+":"+str(token)
                authentication_bytes = authentication.encode('ascii')
                authentication_bytes_base64 = base64.b64encode(authentication_bytes)
                authentication_bytes_base64_decode = authentication_bytes_base64.decode('ascii')
                source_number = client.operator.operator_number
                destination_contact_number = destination_contact.mobile
                no_country_perms = []
                country_not_active = []
                contact_not_active = []
                if not destination_contact.is_active == False:
                    if not destination_contact.country.is_active == False:
                        if destination_contact.country in client.countries.all():
                            if client.credit_limit == client.credit:
                                messages.info(request, "You  have reached your credit limit. Kindly add credits.")
                                notification_entry = Notifications.objects.create(user=self.request.user,notification="You  have reached your credit limit. Kindly add credits.")
                                send_mail('Add your Credits', 'You have reached the credit limits', 'techspeedwise@gmail.com',[client.email], fail_silently=False)
                            if client.operator.code == 'TLX':
                                telnyx.api_key = token
                                mms_message_entry = MMSMessages.objects.create(client=client, user=self.request.user,contact=destination_contact,message_subject=message_subject,message=msg,attachment=request.FILES.get('attachment'))

                                send_msg = telnyx.Message.create(
                                    from_=source_number,
                                    to=country_tele_code+destination_contact_number,
                                    subject=message_subject,
                                    text=msg,
                                    media_urls=['http://localhost:8000'+str(mms_message_entry.attachment.url)],
                                )
                                credit_obj = ClientCreditInOuts.objects.create(amount=1.0, client=client)
                                client.credit-=1
                                client.save()
                            if client.operator.code == 'THQ':
                                mms_message_entry = MMSMessages.objects.create(client=client, user=self.request.user,contact=destination_contact,message_subject=message_subject,message=msg,attachment=request.FILES.get('attachment'))
                                url = "https://api.thinq.com/account/" + str(account_id) + "/product/origination/mms/send"
                                file_path = 'http://localhost:8000' + str(mms_message_entry.attachment.url)
                                payload = "{\n  \"from_did\": \"" + source_number + "\",\n  \"to_did\": \"" + destination_contact_number + "\",\n  \"message\": \"" + str(msg) + "\",\n  \"media_url\": \"" + file_path + "\"}"


                                files = []
                                headers = {
                                    'Authorization': 'Basic ' + str(authentication_bytes_base64_decode),
                                    'Content-Type': 'application/json'
                                }
                                response = requests.request("POST", url, headers=headers, data=payload, files=files)
                                print(response,"rrrrrrrrrr")
                                messages.info(request, response.text.encode('utf8'))
                                credit_obj = ClientCreditInOuts.objects.create(amount=1.0, client=client)
                                client.credit -= 1
                                client.save()
                        else:
                            no_country_perms.append(destination_contact)
                    else:
                        country_not_active.append(destination_contact)
                else:
                    contact_not_active.append(destination_contact)
            if no_country_perms:
                notification = str(len(no_country_perms))+' messages failed. Countries of the contacts are not permitted for the client.'
                notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,client=client,notification=notification)
            if country_not_active:
                notification = str(len(country_not_active)) + ' messages failed. Countries of the contacts are not active.'
                notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,client=client,notification=notification)
            if contact_not_active:
                notification = str(len(contact_not_active)) + ' messages failed. Contacts are not active.'
                notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,client=client,notification=notification)
            action = str(request.user) + ' sent some MMS messages at ' + datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S")
            ActionLogs.objects.create(user=request.user, action=action)
            return redirect('mmsmessaging')
        except:
            messages.error(request, "Something went wrong")
            return redirect('mmsmessaging')


class Templates_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/sms_templates.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Templates_View, self).get_context_data(**kwargs)
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        if self.request.user.is_superuser:
            sms_templates_object = Templates.objects.all()
            notifications = Notifications.objects.all()
            context['notifications'] = notifications
        else:
            if Client.objects.filter(user=self.request.user):
                client = Client.objects.get(user=self.request.user)
            else:
                client = ClientSubUser.objects.get(user=self.request.user).client
            sms_templates_object = Templates.objects.filter(created_by=client)
            notifications = Notifications.objects.filter(client=client)
            context['notifications'] = notifications
        context['templateform'] = TemplateForm
        context['templates'] = sms_templates_object
        return context

    def post(self, request):
        try:
            templateform = TemplateForm(request.POST, request.FILES or None)
            if Client.objects.filter(user=self.request.user):
                client = Client.objects.get(user=self.request.user)
            else:
                client = ClientSubUser.objects.get(user=self.request.user).client
            if templateform.is_valid():
                templates = templateform.save()
                templates.created_by=client
                templates.save()
                action = str(request.user) + ' created message template at ' + datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
            return redirect('templates')
        except:
            messages.error(request, "Something went wrong")
            return redirect('templates')

def delete_template(request, template_pk):
    try:
        template = Templates.objects.get(pk=template_pk)
        template.delete()
        action = str(request.user) + ' deleted a template at ' + datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S")
        ActionLogs.objects.create(user=request.user, action=action)
        return redirect('templates')
    except:
        messages.error(request, "Something went wrong")
        return redirect('templates')


class Country_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/countries.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Country_View, self).get_context_data(**kwargs)
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        if self.request.user.is_superuser:
            countries = Country.objects.all()
            notifications = Notifications.objects.all()
            context['notifications'] = notifications
            context['countryform'] = CountryForm
            context['countries'] = countries
        else:
            messages.info(self.request, "You are not authourized to access this records")
        return context

    def post(self, request):
        try:
            if Country.objects.filter(id=request.POST.get('country_id')):
                country = Country.objects.get(id=request.POST.get('country_id'))
                country.country_name=request.POST.get('name')
                country.country_code=request.POST.get('code')
                country.country_tele_code=request.POST.get('token')
                country.save()
                action = str(request.user) + ' updated a country '+str(country)+' at '+ datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
                return redirect('countries')

            elif request.POST.get('action_type') == 'enable_country':
                country = Country.objects.get(id=request.POST.get('id'))
                print(request.POST.get('is_active'))
                country.is_active = request.POST.get('is_active') == 'true'
                country.save()
                action = str(request.user) + ' enabled/disabled country ' + str(country) + ' at ' + datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S")
                ActionLogs.objects.create(user=request.user, action=action)
                return redirect('countries')
            else:
                countryform = CountryForm(request.POST, request.FILES or None)
                if countryform.is_valid():
                    country = countryform.save()
                    country.save()
                    action = str(request.user) + ' added a country ' + str(country) + ' at ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    ActionLogs.objects.create(user=request.user, action=action)
                return redirect('countries')
        except:
            messages.error(request, "Something went wrong")
            return redirect('countries')


def delete_country(request, country_pk):
    try:
        country = Country.objects.get(pk=country_pk)
        country.delete()
        action = str(request.user) + ' deleted a country ' + str(country) + ' at ' + datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S")
        ActionLogs.objects.create(user=request.user, action=action)
        return redirect('countries')
    except:
        messages.error(request, "Something went wrong")
        return redirect('countries')


class MessageResposeView(APIView):

    def get(self, request,format=None):
        return Response({})


    def post(self, request):
        data = request.data
        values = json.dumps(data)
        values = json.loads(values)
        if values.get('from') and values.get('to'):
            from_contact = Contact.objects.filter(mobile=values.get('from'))
            if from_contact:
                from_contact = Contact.objects.get(mobile=values.get('from'))
                from_message = values.get('message')
                if not Messages.objects.filter(contact=from_contact, message=from_message, is_inbound=True):
                    inbound_message = Messages.objects.create(contact=from_contact,client=from_contact.client,message=from_message, is_inbound=True)
                    notification = 'Message received from '+str(from_contact)
                    notification_entry = Notifications.objects.create(message_out=from_message, user=self.request.user,
                                                                      contact=from_contact, client=from_contact.client,
                                                                      notification=notification)
        if values.get('data') and  values.get('data').get('event_type') == 'message.received':
            from_phone_number = values.get('data').get('payload').get('from').get('phone_number')[-10:]
            from_contact = Contact.objects.filter(mobile=from_phone_number)
            if from_contact:
                from_contact = Contact.objects.get(mobile=from_phone_number)
                from_message = values.get('data').get('payload').get('text')
                if not Messages.objects.create(contact=from_contact,message=from_message,is_inbound=True):
                    inbound_message = Messages.objects.create(contact=from_contact,client=from_contact.client,message=from_message,is_inbound=True)
                    notification = 'Message received from ' + str(from_contact)
                    notification_entry = Notifications.objects.create(message_out=from_message, user=self.request.user,
                                                                      contact=from_contact, client=from_contact.client,
                                                                      notification=notification)
        return redirect('message-response')


class ReportsView(TemplateView):
    template_name = 'smsapp/reports.html'
    login_url = 'login'
    
    def get_context_data(self,*args,**kwargs):
        context = super(ReportsView, self).get_context_data(**kwargs)
        if Client.objects.filter(user=self.request.user):
            logged_client = Client.objects.get(user=self.request.user)
            context['logged_client'] = logged_client
        if ClientSubUser.objects.filter(user=self.request.user):
            logged_client = ClientSubUser.objects.get(user=self.request.user).client
            context['logged_client'] = logged_client
        now = datetime.now()
        last_three_month = now + dateutil.relativedelta.relativedelta(months=-3)
        last_month = now + dateutil.relativedelta.relativedelta(months=-1)
        last_week = now + dateutil.relativedelta.relativedelta(weeks=-1)
        # bar chart start
        if self.request.user.is_superuser:
            delta = now - last_three_month
            periods = []
            sms_telnyx = []
            sms_thinq = []
            mms_telnyx = []
            mms_thinq = []
            for i in range(delta.days):
                week=(last_three_month+dateutil.relativedelta.relativedelta(days=i)).isocalendar()[:2]
                yearweek = '{}/{:02}'.format(*week)
                periods.append(yearweek)
            for i in sorted(set(periods)):
                year=i.split('/')[0]
                week=i.split('/')[1]
                sms_telnyx.append(Messages.objects.filter(is_inbound=False,create_date__year=year,create_date__week=week,client__operator__code='TLX').count())
                sms_thinq.append(Messages.objects.filter(is_inbound=False,create_date__year=year,create_date__week=week,client__operator__code='THQ').count())
                mms_telnyx.append(MMSMessages.objects.filter(is_inbound=False,create_date__year=year,create_date__week=week,client__operator__code='TLX').count())
                mms_thinq.append(MMSMessages.objects.filter(is_inbound=False,create_date__year=year,create_date__week=week,client__operator__code='THQ').count())

            total_sms_sent = Messages.objects.filter(is_inbound=False).count()
            total_sms_sent_telnyx = Messages.objects.filter(is_inbound=False, client__operator__code='TLX').count()
            total_sms_sent_thinq = Messages.objects.filter(is_inbound=False, client__operator__code='THQ').count()

            total_mms_sent = MMSMessages.objects.filter(is_inbound=False).count()
            total_mms_sent_telnyx = MMSMessages.objects.filter(is_inbound=False, client__operator__code='TLX').count()
            total_mms_sent_thinq = MMSMessages.objects.filter(is_inbound=False, client__operator__code='THQ').count()

            total_sms_sent_last_month = Messages.objects.filter(is_inbound=False).filter(create_date__gte=now,create_date__lte=last_month).count()
            total_sms_sent_last_month_telnyx = Messages.objects.filter(is_inbound=False,client__operator__code='TLX').filter(create_date__gte=now,create_date__lte=last_month).count()
            total_sms_sent_last_month_thinq = Messages.objects.filter(is_inbound=False,client__operator__code='THQ').filter(create_date__gte=now,create_date__lte=last_month).count()

            total_mms_sent_last_month = MMSMessages.objects.filter(is_inbound=False).filter(create_date__gte=now,create_date__lte=last_month).count()
            total_mms_sent_last_month_telnyx = MMSMessages.objects.filter(is_inbound=False,client__operator__code='TLX').filter(create_date__gte=now, create_date__lte=last_month).count()
            total_mms_sent_last_month_thinq = MMSMessages.objects.filter(is_inbound=False,client__operator__code='THQ').filter(create_date__gte=now, create_date__lte=last_month).count()

            total_sms_sent_last_week = Messages.objects.filter(is_inbound=False).filter(create_date__gte=now,create_date__lte=last_week).count()
            total_sms_sent_last_week_telnyx = Messages.objects.filter(is_inbound=False,client__operator__code='TLX').filter(create_date__gte=now,create_date__lte=last_week).count()
            total_sms_sent_last_week_thinq = Messages.objects.filter(is_inbound=False,client__operator__code='THQ').filter(create_date__gte=now,create_date__lte=last_week).count()

            total_mms_sent_last_week = MMSMessages.objects.filter(is_inbound=False).filter(create_date__gte=now,create_date__lte=last_week).count()
            total_mms_sent_last_week_telnyx = MMSMessages.objects.filter(is_inbound=False,client__operator__code='TLX').filter(create_date__gte=now, create_date__lte=last_week).count()
            total_mms_sent_last_week_thinq = MMSMessages.objects.filter(is_inbound=False, client__operator__code='THQ').filter(create_date__gte=now, create_date__lte=last_week).count()

            # bar chart end
            # pie chart start
            client_names = []
            sms_sent_by_clients = []
            mms_sent_by_clients = []
            clients = Client.objects.all()
            for client in clients:
                client_names.append(Client.objects.get(id=client.id).user.first_name)
                sms_sent_by_clients.append(Messages.objects.filter(is_inbound=False,client=client).count())
                mms_sent_by_clients.append(MMSMessages.objects.filter(is_inbound=False,client=client).count())
            # pie chart end

            context['client_names'] = client_names
            context['sms_sent_by_clients'] = sms_sent_by_clients
            context['sms_sent_by_clients'] = sms_sent_by_clients

            context['total_sms_sent'] = total_sms_sent
            context['total_sms_sent_telnyx'] = total_sms_sent_telnyx
            context['total_sms_sent_thinq'] = total_sms_sent_thinq
            context['total_mms_sent'] = total_mms_sent
            context['total_mms_sent_telnyx'] = total_mms_sent_telnyx
            context['total_mms_sent_thinq'] = total_mms_sent_thinq
            context['total_sms_sent_last_month'] = total_sms_sent_last_month
            context['total_sms_sent_last_month_telnyx'] = total_sms_sent_last_month_telnyx
            context['total_sms_sent_last_month_thinq'] = total_sms_sent_last_month_thinq
            context['total_mms_sent_last_month'] = total_mms_sent_last_month
            context['total_mms_sent_last_month_telnyx'] = total_mms_sent_last_month_telnyx
            context['total_mms_sent_last_month_thinq'] = total_mms_sent_last_month_thinq
            context['total_sms_sent_last_week'] = total_sms_sent_last_week
            context['total_sms_sent_last_week_telnyx'] = total_sms_sent_last_week_telnyx
            context['total_sms_sent_last_week_thinq'] = total_sms_sent_last_week_thinq
            context['total_mms_sent_last_week'] = total_mms_sent_last_week
            context['total_mms_sent_last_week_telnyx'] = total_mms_sent_last_week_telnyx
            context['total_mms_sent_last_week_thinq'] = total_mms_sent_last_week_thinq
            context['sms_telnyx'] = sms_telnyx
            context['sms_thinq'] = sms_thinq
            context['mms_telnyx'] = mms_telnyx
            context['mms_telnyx'] = mms_telnyx
            context['period'] = sorted(set(periods))
        else:
            total_sms_sent = Messages.objects.filter(is_inbound=False,client=logged_client).count()
            total_sms_sent_last_month = Messages.objects.filter(is_inbound=False,client=logged_client).filter(create_date__gte=now,create_date__lte=last_month).count()
            total_sms_sent_last_week = Messages.objects.filter(is_inbound=False,client=logged_client).filter(create_date__gte=now,create_date__lte=last_month).count()

            delta = now - last_three_month
            periods = []
            sms_out = []
            sms_in = []
            for i in range(delta.days):
                week = (last_three_month + dateutil.relativedelta.relativedelta(days=i)).isocalendar()[:2]
                yearweek = '{}/{:02}'.format(*week)
                periods.append(yearweek)
            for i in sorted(set(periods)):
                year = i.split('/')[0]
                week = i.split('/')[1]
                sms_out.append(Messages.objects.filter(is_inbound=False, create_date__year=year, create_date__week=week,client=logged_client).count())
                sms_in.append(Messages.objects.filter(is_inbound=True, create_date__year=year, create_date__week=week,client=logged_client).count())

            # pie chart start
            contact_group_names = []
            sms_sent_by_contact_groups = []
            mms_sent_by_contact_groups = []
            contact_groups = ContactGroup.objects.filter(client=logged_client)
            for contact_group in contact_groups:
                contact_group_names.append(ContactGroup.objects.get(id=contact_group.id).name)
                sms_sent_by_contact_groups.append(Messages.objects.filter(is_inbound=False,contact__group=contact_group).count())
                mms_sent_by_contact_groups.append(MMSMessages.objects.filter(is_inbound=False,contact__group=contact_group).count())
            # pie chart end

            context['total_sms_sent']=total_sms_sent
            context['total_sms_sent_last_month']=total_sms_sent_last_month
            context['total_sms_sent_last_week']=total_sms_sent_last_week
            context['sms_out']=sms_out
            context['sms_in']=sms_in
            context['period'] = sorted(set(periods))
        return context