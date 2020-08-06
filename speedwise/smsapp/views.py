from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from .models import *
import pandas as pd
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


class DashboardView(TemplateView):
    template_name = 'smsapp/index.html'

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
                        authy_api = AuthyApiClient(settings.AUTHY_API_CLIENT)
                        user = authy_api.users.create(email=user.email,phone=client.mobile,country_code=client.country.country_tele_code)
                        if user.ok():
                            client.authy_id=user.id
                            client.save()
                        else:
                            print(user.errors())
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
                client.credit_in = request.POST.get('credin', '')
                client.credit_out = request.POST.get('credout', '')
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
                authy_api = AuthyApiClient(settings.AUTHY_API_CLIENT)
                user = authy_api.users.create(email=user.email, phone=client.mobile,
                                              country_code=client.country.country_tele_code)
                if user.ok():
                    client.authy_id = user.id
                    client.save()
                else:
                    print(user.errors())
                return redirect('clients')

        except:
            messages.error(request,"Something went wrong")
            return redirect('clients')

def delete_user(request, user_pk):
    try:
        user = Client.objects.get(pk=user_pk).user
        user.delete()
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
                clientsubuser = clientsubuserform.save()
                clientsubuser.user = user
                clientsubuser.save()
                authy_api = AuthyApiClient(settings.AUTHY_API_CLIENT)
                user = authy_api.users.create(email=user.email, phone=clientsubuser.mobile,
                                              country_code=clientsubuser.country.country_tele_code)
                if user.ok():
                    clientsubuser.authy_id = user.id
                    clientsubuser.save()
                else:
                    print(user.errors())
            return redirect('clientprofile',request.POST.get('client'))
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
            password = request.POST.get('password', '')
            username = User.objects.get(email=email.lower()).username
            authy_api = AuthyApiClient(settings.AUTHY_API_CLIENT)
            if username and password:
                user = authenticate(username=username, password=password)
                if user is not None:
                    print(user)
                    if user.is_superuser:
                        try:
                            authy_id = int(settings.SUPER_ADMIN_AUTHY_ID)
                            sms = authy_api.users.request_sms(authy_id,{'force': True})
                            return render(request, 'smsapp/verify-2fa-token.html',{'authy_id': authy_id, 'user': user.id})
                        except:
                            messages.error(request, "Something went wrong")
                            return redirect('login')

                    else:
                        if ClientSubUser.objects.filter(user = user):
                            if ClientSubUser.objects.get(user = user).is_active:
                                try:
                                    authy_id = int(ClientSubUser.objects.get(user=user).authy_id)
                                    sms = authy_api.users.request_sms(authy_id,{'force': True})
                                    return render(request, 'smsapp/verify-2fa-token.html',{'authy_id': authy_id, 'user': user.id})
                                except:
                                    messages.error(request, "Something went wrong")
                                    return redirect('login')
                            else:
                                messages.error(request,"Contact administrator to activate the account")
                                return redirect('login')
                        else:
                            if Client.objects.filter(user = user):
                                if Client.objects.get(user = user).is_active:
                                    try:
                                        authy_id = int(Client.objects.get(user=user).authy_id)
                                        sms = authy_api.users.request_sms(authy_id,{'force': True})
                                        return render(request, 'smsapp/verify-2fa-token.html',{'authy_id': authy_id, 'user': user.id})
                                    except:
                                        messages.error(request, "Something went wrong")
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


def verify_2fa_token(request):
    try:
        authy_api = AuthyApiClient(settings.AUTHY_API_CLIENT)
        user = User.objects.get(id=request.POST.get('user'))
        authy_id=int(request.POST.get('authy_id'))
        token = str(request.POST.get('token'))
        verification = authy_api.tokens.verify(authy_id,token=token)
        if verification.ok():
            login(request,user)
            return redirect('index')
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
    print(request)
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('login'))

class ClientProfile(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/client_profile.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(ClientProfile, self).get_context_data(**kwargs)
        client_object = Client.objects.get(pk=kwargs['user_pk'])
        countries = client_object.countries.all()
        all_countries= Country.objects.all()
        if self.request.user.is_superuser:
            client_sub_user_objects = ClientSubUser.objects.all()
            userform = UsercreateForm
            clientsubuserform = ClientSubUserForm
            context['clientsubusers'] = client_sub_user_objects
            context['clientsubuserform'] = clientsubuserform
            context['userform'] = userform
        else:
            client_sub_user_objects = ClientSubUser.objects.filter(client=Client.objects.get(user=self.request.user))
            print(client_sub_user_objects)
            userform = UsercreateForm
            clientsubuserform = ClientSubUserForm
            context['clientsubusers'] = client_sub_user_objects
            context['clientsubuserform'] = clientsubuserform
            context['userform'] = userform
            
        context['client'] = client_object
        context['countries']= countries
        context['cntry']=all_countries
        return context

    def post(self,request,user_pk):
        if request.method == "POST":
            client = Client.objects.get(pk=user_pk)
            client.user = User.objects.get(pk=request.POST.get('client_user'))
            client.email = request.POST.get('client_email')
            client.operator = request.POST.get('client_operator')
            client.save()


def add_client_credit(request,user_pk):
    try:
        client_object = Client.objects.get(pk=user_pk)
        credit_amount = request.POST.get('credit')
        client_object.credit_in+=float(credit_amount)
        client_object.save()
        return redirect('clientprofile',user_pk)
    except:
        messages.error(request, "Something went wrong")
        return redirect('clientprofile', user_pk)

def remove_client_credit(request,user_pk):
    try:
        client_object = Client.objects.get(pk=user_pk)
        remove_amount = request.POST.get('removecredit')
        client_object.credit_in-=float(remove_amount)
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
        if self.request.user.is_superuser:
            operators = Operator.objects.all()
            context['operators'] = operators
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
            if self.request.user.is_superuser:
                clients = Client.objects.all()
                countries = Country.objects.all()
                contacts = Contact.objects.all()
                context['contactsform'] = contactform
                context['contacts'] = contacts
                context['clients'] = clients
                context['countries'] = countries
            else:
                if Client.objects.filter(user=self.request.user):
                    client = Client.objects.get(user=self.request.user)
                else:
                    client = ClientSubUser.objects.get(user=self.request.user).client
                countries = Country.objects.all() #Need to filter based on clients
                contacts = Contact.objects.filter(client=client)
                context['contactsform'] = contactform
                context['contacts'] = contacts
                context['countries'] = countries
        else:
            pass
        
        return context

    def post(self, request):
        try:
            if Contact.objects.filter(id=request.POST.get('contact_id')):
                print(request.POST)
                contact = Contact.objects.get(id=request.POST.get('contact_id'))
                contact.name = request.POST.get('name')
                contact.mobile = request.POST.get('mobile')
                contact.country = Country.objects.get(pk=request.POST.get('country'))
                if Client.objects.filter(user=self.request.user):
                    contact.client = Client.objects.get(user=self.request.user)
                elif ClientSubUser.objects.filter(user=self.request.user):
                    contact.client = ClientSubUser.objects.get(user=self.request.user).client
                else:
                    None
                contact.save()
                return redirect('contacts')
            elif request.POST.get('action_type') == 'enable_contact':
                print(request.POST.get('id'),request.POST.get('is_active'))
                contact = Contact.objects.get(id=request.POST.get('id'))
                contact.is_active = request.POST.get('is_active') == 'true'
                contact.save()
                return redirect('contacts')
            else:
                contactsform = ContactForm(request.POST, request.FILES or None)
                if contactsform.is_valid():
                    contacts = contactsform.save()
                    if Client.objects.filter(user=self.request.user):
                        client = Client.objects.get(user=self.request.user)
                    elif ClientSubUser.objects.filter(user=self.request.user).client:
                        client = ClientSubUser.objects.get(user=self.request.user).client
                    else:
                        None
                    mobile = [character for character in str(contacts.mobile) if character.isalnum()]
                    contacts.mobile = "".join(mobile)
                    contacts.client=client
                    contacts.user=self.request.user
                    contacts.save()
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
                    mobile = [character for character in str(j[1]) if character.isalnum()]
                    mobile = "".join(mobile)
                    if not Contact.objects.filter(name=j[0], mobile=mobile):
                        contact = Contact.objects.create(name=j[0], mobile=mobile, client=client, user=user,
                                                         country=country)
                        contact.save()
                elif ClientSubUser.objects.filter(user=request.user):
                    client = ClientSubUser.objects.get(user=request.user).client
                    user = request.user
                    country = Country.objects.get(country_code=j[2])
                    mobile = [character for character in str(j[1]) if character.isalnum()]
                    mobile = "".join(mobile)
                    if not Contact.objects.filter(name=j[0], mobile=mobile):
                        contact = Contact.objects.create(name=j[0], mobile=mobile, client=client, user=user,
                                                         country=country)
                        contact.save()
                else:
                    user = request.user
                    country = Country.objects.get(country_code=j[2])
                    mobile = [character for character in str(j[1]) if character.isalnum()]
                    mobile = "".join(mobile)
                    if not Contact.objects.filter(name=j[0], mobile=mobile):
                        contact = Contact.objects.create(name=j[0], mobile=mobile, user=user,country=country)
                        contact.save()
            return redirect('contacts')

    except:
        messages.error(request, "Something went wrong")
        return redirect('contacts')

def delete_contact(request, contact_pk):
    try:
        contact = Contact.objects.get(pk=contact_pk)
        contact.delete()
        return redirect('contacts')
    except:
        messages.error(request, "Something went wrong")
        return redirect('contacts')

class Messages_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/messages.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Messages_View, self).get_context_data(**kwargs)
        messagingform = MessagesForm
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

        templates = Templates.objects.all()
        context['messagingform'] = messagingform
        context['messageslist'] = messages
        context['contacts'] = contacts
        context['templates'] = templates
        return context


    def post(self, request):
        try:
            contacts = request.POST.get('contactsList')
            destination_contacts = contacts.split(",")
            msg = request.POST.get("message_out")
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
                if not destination_contact.is_active == False:
                    if not destination_contact.country.is_active == False:
                        if destination_contact.country in client.countries.all():
                            if client.credit_limit == (client.credit_in - client.credit_out):
                                messages.info(request, "You  have reached your credit limit. Kindly add credits.")
                                send_mail('Add your Credits', 'You have reached the credit limits', 'techspeedwise@gmail.com',[client.email], fail_silently=False)
                                if client.operator.code == 'TLX':
                                    telnyx.api_key = token
                                    send_msg = telnyx.Message.create(
                                        from_=source_number,
                                        to=country_tele_code+destination_contact_number,
                                        text=msg,
                                    )
                                    message_entry = Messages.objects.create(client=client,user=self.request.user,contact=destination_contact,message_out=msg,message_telnyx_id=send_msg.get('id'))
                                    client.credit_out+=1
                                    client.save()
                                if client.operator.code == 'THQ':
                                    url = "https://api.thinq.com/account/" + str(
                                        account_id) + "/product/origination/sms/send"
                                    payload = "{\n  \"from_did\": \"" + source_number + "\",\n  \"to_did\": \"" + source_number + "\",\n  \"message\": \"" + str(
                                        msg) + "\"\n}"
                                    headers = {
                                        'Authorization': 'Basic ' + str(authentication_bytes_base64_decode),
                                        'Content-Type': 'application/json'
                                    }
                                    response = requests.request("POST", url, headers=headers, data=payload)
                                    messages.info(request, response.text.encode('utf8'))
                                    message_entry = Messages.objects.create(client=client, user=self.request.user,
                                                                            contact=destination_contact, message_out=msg)
                                    client.credit_out += 1
                                    client.save()
                            else:
                                if client.operator.code == 'TLX':
                                    telnyx.api_key = token
                                    send_msg = telnyx.Message.create(
                                        from_=source_number,
                                        to=country_tele_code+destination_contact_number,
                                        text=msg,
                                    )
                                    message_entry = Messages.objects.create(client=client,user=self.request.user,contact=destination_contact,message_telnyx_id=send_msg.get('id'),message_out=msg)
                                    client.credit_out += 1
                                    client.save()
                                if client.operator.code == 'THQ':
                                    url = "https://api.thinq.com/account/" + str(account_id) + "/product/origination/sms/send"
                                    payload = "{\n  \"from_did\": \""+source_number+"\",\n  \"to_did\": \""+source_number+"\",\n  \"message\": \"" +str(msg)+ "\"\n}"
                                    headers = {
                                        'Authorization': 'Basic '+str(authentication_bytes_base64_decode),
                                        'Content-Type': 'application/json'
                                    }
                                    response = requests.request("POST", url, headers=headers, data=payload)
                                    messages.info(request, response.text.encode('utf8'))
                                    message_entry = Messages.objects.create(client=client,user=self.request.user,contact=destination_contact,message_out=msg)
                                    client.credit_out += 1
                                    client.save()
                        else:
                            notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,
                                                                    contact=destination_contact, client=client,notification="The country is not permitted for the client")
                    else:
                        notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,
                                                                          contact=destination_contact, client=client,
                                                                          notification="The country is not activated for this contact")
                else:
                    notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,
                                                                      contact=destination_contact, client=client,
                                                                      notification="The contact is not activated")
            return redirect('messaging')
        except:
            messages.error(request, "Something went wrong")
            return redirect('messaging')


def delete_message(request, message_pk):
    try:
        message = Messages.objects.get(pk=message_pk)
        message.delete()
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
            mmsmessages = Messages.objects.filter(client=client)
        templates = Templates.objects.all()
        context['mmsmessagingform'] = mmsmessagingform
        context['mmsmessageslist'] = mmsmessages
        context['contacts'] = contacts
        context['templates'] = templates
        return context

    def post(self, request):
        try:
            contacts = request.POST.get('contactsList')
            destination_contacts = contacts.split(",")
            message_subject = request.POST.get("message_subject")
            msg = request.POST.get("message_out")
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
                if not destination_contact.is_active == False:
                    if not destination_contact.country.is_active == False:
                        if destination_contact.country in client.countries.all():
                            if client.credit_limit == (client.credit_in - client.credit_out):
                                messages.info(request, "You  have reached your credit limit. Kindly add credits.")
                                send_mail('Add your Credits', 'You have reached the credit limits', 'techspeedwise@gmail.com',[client.email], fail_silently=False)
                                if client.operator.code == 'TLX':
                                    telnyx.api_key = token
                                    send_msg = telnyx.Message.create(
                                        from_=source_number,
                                        to=country_tele_code+destination_contact_number,
                                        subject=message_subject,
                                        text=msg,
                                        media_urls=['http://localhost:8000/media/media/mmsattachments/amazon.jpg'],
                                    )
                                    mms_message_entry = MMSMessages.objects.create(client=client,user=self.request.user,contact=destination_contact,message_subject=message_subject,message_out=msg,message_telnyx_id=send_msg.get('id'))
                                    client.credit_out+=1
                                    client.save()
                            else:
                                if client.operator.code == 'TLX':
                                    telnyx.api_key = token
                                    send_msg = telnyx.Message.create(
                                        from_=source_number,
                                        to=country_tele_code+destination_contact_number,
                                        subject=message_subject,
                                        text=msg,
                                        media_urls=['http://localhost:8000/media/media/mmsattachments/amazon.jpg'],
                                    )
                                    mms_message_entry = MMSMessages.objects.create(client=client,user=self.request.user,contact=destination_contact,message_subject=message_subject,message_out=msg,message_telnyx_id=send_msg.get('id'))
                                    client.credit_out += 1
                                    client.save()

                        else:
                            notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,
                                                                    contact=destination_contact, client=client,notification="The country is not permitted for the client")
                    else:
                        notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,
                                                                          contact=destination_contact, client=client,
                                                                          notification="The country is not activated for this contact")
                else:
                    notification_entry = Notifications.objects.create(message_out=msg, user=self.request.user,
                                                                      contact=destination_contact, client=client,
                                                                      notification="The contact is not activated")
            return redirect('mmsmessaging')
        except:
            messages.error(request, "Something went wrong")
            return redirect('mmsmessaging')


class Templates_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/sms_templates.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Templates_View, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            sms_templates_object = Templates.objects.all()
        else:
            if Client.objects.filter(user=self.request.user):
                client = Client.objects.get(user=self.request.user)
            else:
                client = ClientSubUser.objects.get(user=self.request.user).client
            sms_templates_object = Templates.objects.filter(created_by=client)
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
            return redirect('templates')
        except:
            messages.error(request, "Something went wrong")
            return redirect('templates')

def delete_template(request, template_pk):
    try:
        template = Templates.objects.get(pk=template_pk)
        template.delete()
        return redirect('templates')
    except:
        messages.error(request, "Something went wrong")
        return redirect('templates')


class Country_View(LoginRequiredMixin,TemplateView):
    template_name = 'smsapp/countries.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(Country_View, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            countries = Country.objects.all()
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
                return redirect('countries')

            elif request.POST.get('action_type') == 'enable_country':
                country = Country.objects.get(id=request.POST.get('id'))
                country.is_active = request.POST.get('is_active') == 'true'
                country.save()
                return redirect('countries')
            else:
                countryform = CountryForm(request.POST, request.FILES or None)
                if countryform.is_valid():
                    country = countryform.save()
                    country.save()
                return redirect('countries')
        except:
            messages.error(request, "Something went wrong")
            return redirect('countries')


def delete_country(request, country_pk):
    try:
        country = Country.objects.get(pk=country_pk)
        country.delete()
        return redirect('countries')
    except:
        messages.error(request, "Something went wrong")
        return redirect('countries')


class MessageResposeView(APIView):

    def get(self, request,format=None):
        return Response({})


    def post(self, request,format=None):
        values = request.data
        webhook_response = WebhookResponse.objects.create(message_response=values)
        webhook_response.save()
        return redirect('message-response')


class ReportsView(TemplateView):
    template_name = 'smsapp/reports.html'
    login_url = 'login'
    
    def get_context_data(self,*args,**kwargs):
        context = super(ReportsView, self).get_context_data(**kwargs)
        return context