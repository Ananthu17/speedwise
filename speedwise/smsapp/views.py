from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .forms import ClientForm,UsercreateForm,OperatorForm,ContactForm,MessagesForm
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
        context['clients'] = client_objects
        return context

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
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            if username and password:
                user = authenticate(username=username, password=password)

                if user is not None:
                    login(request, user)
                    return redirect('index')
                else:
                    messages.error(request,
                                   "Username or password does not match,please retry with correct credentaials")
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
        context['client'] = client_object
        return context


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
        contacts = Contact.objects.all()
        context['contactsform'] = contactform
        context['contacts'] = contacts
        return context

    def post(self, request):
        try:
            contactsform = ContactForm(request.POST, request.FILES or None)
            if contactsform.is_valid():
                contacts = contactsform.save()
                contacts.save()
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
        contacts = Contact.objects.all()
        context['messagingform'] = messagingform
        context['messages'] = messages
        context['contacts'] = contacts
        return context

    def post(self, request):
        try:
            destination_contacts = [request.POST.get('contactsList')]
            client = Client.objects.get(pk=request.POST.get("client"))
            token = client.operator.token
            source_number = client.operator.operator_number
            msg = request.POST.get("message_out")
            for item in destination_contacts:
                destination_contact = Contact.objects.get(id=item)
                print(destination_contact)
                destination_contact_number = destination_contact.mobile
                telnyx.api_key = token
                telnyx.Message.create(
                    from_=source_number,
                    to=destination_contact_number,
                    text=msg,
                )
                message_entry = Messages.objects.create(client=client, contact=destination_contact,message_out=msg)
                print(message_entry)

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

def edit_message(request,message_pk):
    message = Messages.objects.get(pk=message_pk)
    if request.method == "POST":
        form = MessagesForm(request.POST,instance=message)
        if form.is_valid():
            form.save()
            return redirect('messaging')
    else:
        form = MessagesForm(instance=message)
        print(form)
        return redirect(request,'messages.html',{form:form})


