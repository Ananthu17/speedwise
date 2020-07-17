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
from django.contrib.auth.decorators import login_required
from .forms import ClientForm,UsercreateForm,OperatorForm,ContactForm,MessagesForm,TemplateForm,CountryForm
import telnyx


class DashboardView(TemplateView):
    template_name = 'smsapp/index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        else:
            context = super(DashboardView, self).dispatch(request, *args, **kwargs)
        return context


class ClientView(TemplateView):
    template_name = 'smsapp/clients.html'

    def get_context_data(self, **kwargs):
        context = super(ClientView, self).get_context_data(**kwargs)
        client_objects = Client.objects.all()
        clientform = ClientForm
        userform = UsercreateForm
        context['clients'] = client_objects
        context['clientform'] = clientform
        context['userform'] = userform
        return context

    def post(self,request):
        try:
            clientform = ClientForm(request.POST,request.FILES or None)

            userform = UsercreateForm(request.POST or None)

            if userform.is_valid() and clientform.is_valid():
                user = userform.save()
                user.is_staff = False
                user.save()
                client = clientform.save()
                client.user=user
                print(client)
                client.save()


            return redirect('clients')
        except:
            messages.error(request,"Somethin went wrong")
            return redirect('clients')

def delete_user(request, user_pk):
    try:
        user = Client.objects.get(pk=user_pk).user
        user.delete()
        return redirect('clients')
    except:
        messages.error(request, "Something went wrong")
        return redirect('clients')

def edit_user(request,user_pk):
    user = Client.objects.get(pk=user_pk)
    if request.method == "POST":
        form = ClientForm(request.POST,instance=user)
        if form.is_valid():
            form.save()
            return redirect('clients')
    else:
        form = ClientForm(instance=user)
        print(form)
        return redirect(request,'clients.html',{form:form})

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
            username = Client.objects.get(email=email.lower()).user.username
            print(username,password)
            if username and password:
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('index')
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
                           "Username or password does not match,please retry with correct credentaials")
            return redirect('login')


def register(request):
    if request.method == 'POST':
        first_name =request.POST['first_name']
        last_name =request.POST['last_name']
        mobile =request.POST['mobile']
        email =request.POST['email']
        username =request.POST['username']
        password1 =request.POST['password1']
        password2 =request.POST['password2']
        logo =request.POST['logo']
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request,'User already exists')
                return render(request, 'smsapp/register.html')
            elif Client.objects.filter(email=email).exists():
                messages.info(request, 'Email already taken')
                return render(request, 'smsapp/register.html')
            else:
                user = User.objects.create_user(username=username,password=password1,first_name=first_name,last_name=last_name)
                user.save()
                client = Client.objects.create(user=user,mobile=mobile,email=email)
                client.save()
                return redirect(reverse('login'))
        else:
            messages.info(request,'password not matching')
            return render(request, 'smsapp/register.html')
    else:
        return render(request,'smsapp/register.html')

def logout_view(request):
    print(request)
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('login'))

class ClientProfile(TemplateView):
    template_name = 'smsapp/client_profile.html'

    def get_context_data(self, **kwargs):
        context = super(ClientProfile, self).get_context_data(**kwargs)
        client_object = Client.objects.get(pk=kwargs['user_pk'])
        # print(client_object.countries.all(),"ffffffff")
        # for item in client_object.countries.all():
        #     print(item)
        context['client'] = client_object
        return context

    # def post(self,request,user_pk):
    #     if request.method == "POST":
    #         client = Operator.objects.get(pk=user_pk)
    #         client.user = User.objects.get(pk=request.POST.get('client_user'))
    #         client.email = request.POST.get('client_email')
    #         client.operator = request.POST.get('client_operator')
    #         client.save()


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
        allowed_countries = request.POST.get('allowed_countries')
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



class Operators(TemplateView):
    template_name = 'smsapp/operators.html'

    def get_context_data(self, **kwargs):
        context = super(Operators, self).get_context_data(**kwargs)
        operatorform = OperatorForm
        operators = Operator.objects.all()
        context['operatorform'] = operatorform
        context['operators'] = operators
        return context

    def post(self,request):
        try:
            operatorform = OperatorForm(request.POST,request.FILES or None)
            if operatorform.is_valid():
                operator = operatorform.save()
                operator.save()
            return redirect('operators')
        except:
            messages.error(request,"Something went wrong")
            return redirect('operators')

class OperatorProfile(TemplateView):
    template_name = 'smsapp/operator_profile.html'

    def get_context_data(self, **kwargs):
        context = super(OperatorProfile, self).get_context_data(**kwargs)
        operator_object = Operator.objects.get(pk=kwargs['operator_pk'])
        context['operator'] = operator_object
        return context

    def post(self,request,operator_pk):
        if request.method == "POST":
            operator = Operator.objects.get(pk=operator_pk)
            operator.name = request.POST.get('operator_name')
            operator.code = request.POST.get('operator_code')
            operator.token = request.POST.get('operator_token')
            operator.operator_number = request.POST.get('operator_operator_number')
            operator.save()


def delete_operator(request, operator_pk):
    try:
        operator = Operator.objects.get(pk=operator_pk)
        operator.delete()
        return redirect('operators')
    except:
        messages.error(request, "Something went wrong")
        return redirect('operators')

def edit_operator(request,operator_pk):
    operator = Operator.objects.get(pk=operator_pk)
    if request.method == "POST":
        form = OperatorForm(request.POST,instance=operator)
        if form.is_valid():
            form.save()
            return redirect('operators')
    else:
        form = OperatorForm(instance=operator)
        print(form)
        return redirect(request,'operators.html',{form:form})


class Contacts_View(TemplateView):
    template_name = 'smsapp/contacts.html'

    def get_context_data(self, **kwargs):
        context = super(Contacts_View, self).get_context_data(**kwargs)
        contactform = ContactForm
        user=self.request.user
        if user.is_authenticated:
            if self.request.user.is_superuser:
                contacts = Contact.objects.all()
            else:
                client = Client.objects.get(user=self.request.user)
                contacts = Contact.objects.filter(client=client)
                context['contactsform'] = contactform
                context['contacts'] = contacts
        else:
            pass
        
        return context

    def post(self, request):
        try:
            contactsform = ContactForm(request.POST, request.FILES or None)
            if contactsform.is_valid():
                contacts = contactsform.save()
                mobile = [character for character in str(contacts.mobile) if character.isalnum()]
                contacts.mobile = "".join(mobile)
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
                data = pd.read_excel(file)
            for i,j in data.iterrows():
                if i not in [0,1,2]:
                    if not request.user.is_superuser:
                        client = Client.objects.get(user=request.user)
                        country = Country.objects.get(country_code=j[2])
                        mobile = [character for character in str(j[1]) if character.isalnum()]
                        mobile = "".join(mobile)
                        if not Contact.objects.filter(name=j[0],mobile=mobile):
                            contact = Contact.objects.create(name=j[0],mobile=mobile,client=client,country=country)
                            contact.save()
                    else:
                        country = Country.objects.get(country_code=j[3])
                        mobile = [character for character in str(j[1]) if character.isalnum()]
                        mobile = "".join(mobile)
                        client = Client.objects.filter(name=j[2])
                        if not Contact.objects.filter(name=j[0],mobile=mobile):
                            contact = Contact.objects.create(name=j[0],mobile=mobile,client=client,country=country)
                            contact.save()
            return redirect('contacts')

    except:
        messages.error(request, "Something went wrong")
        return redirect('contacts')

class ContactProfile(TemplateView):
    template_name = 'smsapp/contact_profile.html'

    def get_context_data(self, **kwargs):
        context = super(ContactProfile, self).get_context_data(**kwargs)
        contact_object = Contact.objects.get(pk=kwargs['contact_pk'])
        context['contact'] = contact_object
        return context

    def post(self,request,contact_pk):
        if request.method == "POST":
            contact = Operator.objects.get(pk=contact_pk)
            contact.name = request.POST.get('operator_name')
            contact.mobile = request.POST.get('operator_mobile')
            contact.client = Contact.objects.get(pk=request.POST.get('operator_client'))
            contact.save()


def delete_contact(request, contact_pk):
    try:
        contact = Contact.objects.get(pk=contact_pk)
        contact.delete()
        return redirect('contacts')
    except:
        messages.error(request, "Something went wrong")
        return redirect('contacts')

def edit_contact(request,contact_pk):
    contact = Contact.objects.get(pk=contact_pk)
    if request.method == "POST":
        form = ContactForm(request.POST,instance=contact)
        if form.is_valid():
            form.save()
            return redirect('contacts')
    else:
        form = ContactForm(instance=contact)
        print(form)
        return redirect(request,'contacts.html',{form:form})



class Messages_View(TemplateView):
    template_name = 'smsapp/messages.html'

    def get_context_data(self, **kwargs):
        context = super(Messages_View, self).get_context_data(**kwargs)
        messagingform = MessagesForm
        messages = Messages.objects.all()
        print(messages)
        contacts = Contact.objects.all()
        templates = Templates.objects.all()
        context['messagingform'] = messagingform
        context['messages'] = messages
        context['contacts'] = contacts
        return context

    def post(self, request):
        try:
            contacts = request.POST.get('contactsList')
            destination_contacts = contacts.split(",")
            print(destination_contacts)
            client = Client.objects.get(pk=request.POST.get("client"))
            token = client.operator.token
            source_number = client.operator.operator_number
            msg = request.POST.get("message_out")
            if client.credit_limit == (client.credit_in-client.credit_out):
                messages.info(request,"You  have reached your credit limit. Kindly add credits.")
                send_mail('Add your Credits','You have reached the credit limits','techspeedwise@gmail.com',[client.email], fail_silently=False)
                for item in destination_contacts:
                    destination_contact = Contact.objects.get(id=item)
                    if not destination_contact.is_active == False and destination_contact.country.is_active == False:
                        # Need to cross check country many to many
                        if destination_contact.country in client.countries.all():
                            destination_contact_number = destination_contact.mobile
                            telnyx.api_key = token
                            telnyx.Message.create(
                                from_=source_number,
                                to=destination_contact_number,
                                text=msg,
                            )
                            message_entry = Messages.objects.create(client=client, contact=destination_contact,message_out=msg)
            else:
                for item in destination_contacts:
                    destination_contact = Contact.objects.get(id=item)
                    if not destination_contact.is_active == False and destination_contact.country.is_active == False:
                        # Need to cross check country many to many
                        if destination_contact.country in client.countries.all():
                            destination_contact_number = destination_contact.mobile
                            telnyx.api_key = token
                            telnyx.Message.create(
                                from_=source_number,
                                to=destination_contact_number,
                                text=msg,
                            )
                            message_entry = Messages.objects.create(client=client, contact=destination_contact,message_out=msg)
            return redirect('messaging')
        except:
            messages.error(request, "Something went wrong")
            return redirect('messaging')


class MessageProfile(TemplateView):
    template_name = 'smsapp/message_profile.html'

    def get_context_data(self, **kwargs):
        context = super(MessageProfile, self).get_context_data(**kwargs)
        message_object = Messages.objects.get(pk=kwargs['message_pk'])
        context['message'] = message_object
        return context

def delete_message(request, message_pk):
    try:
        message = Messages.objects.get(pk=message_pk)
        message.delete()
        return redirect('messaging')
    except:
        messages.error(request, "Something went wrong")
        return redirect('messaging')

class Templates_View(TemplateView):
    template_name = 'smsapp/sms_templates.html'

    def get_context_data(self, **kwargs):
        context = super(Templates_View, self).get_context_data(**kwargs)
        sms_templates_object = Templates.objects.all()
        context['templateform'] = TemplateForm
        context['templates'] = sms_templates_object
        return context

    def post(self, request):
        try:
            templateform = TemplateForm(request.POST, request.FILES or None)
            print(templateform)
            if templateform.is_valid():
                templates = templateform.save()
                templates.save()
            return redirect('templates')
        except:
            messages.error(request, "Something went wrong")
            return redirect('templates')

class Country_View(TemplateView):
    template_name = 'smsapp/countries.html'

    def get_context_data(self, **kwargs):
        context = super(Country_View, self).get_context_data(**kwargs)
        countries = Country.objects.all()
        context['countryform'] = CountryForm
        context['countries'] = countries
        return context

    def post(self, request):
        try:
            countryform = CountryForm(request.POST, request.FILES or None)
            if countryform.is_valid():
                country = countryform.save()
                country.save()
            return redirect('countries')
        except:
            messages.error(request, "Something went wrong")
            return redirect('countries')
