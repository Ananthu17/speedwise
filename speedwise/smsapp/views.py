from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .forms import ClientForm,UsercreateForm,OperatorForm,ContactForm,MessagesForm


class DashboardView(TemplateView):
    template_name = 'smsapp/index.html'


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
                client.save()
            return redirect('clients')
        except:
            messages.error(request,"Somethin went wrong")


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

class Messages_View(TemplateView):
    template_name = 'smsapp/messages.html'

    def get_context_data(self, **kwargs):
        context = super(Messages_View, self).get_context_data(**kwargs)
        messagingform = MessagesForm
        messages = Messages.objects.all()
        context['messagingform'] = messagingform
        context['messages'] = messages
        return context

    def post(self, request):
        try:
            messagesform = MessagesForm(request.POST, request.FILES or None)
            if messagesform.is_valid():
                message= messagesform.save()
                message.save()
            return redirect('messaging')
        except:
            messages.error(request, "Something went wrong")
            return redirect('messaging')