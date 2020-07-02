from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .forms import ClientForm,UsercreateForm,OperatorForm


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
    user = Client.objects.get(pk=user_pk).user
    user.delete()
    return redirect('clients')

def edit_user(request,user_pk):
    return redirect('clients')

class ClientProfile(TemplateView):
    template_name = 'smsapp/client_profile.html'

    def get_context_data(self, **kwargs):
        context = super(ClientProfile, self).get_context_data(**kwargs)
        client_object = Client.objects.get(pk=kwargs['user_pk'])
        context['client'] = client_object
        return context


def add_client_credit(request,user_pk):
    client_object = Client.objects.get(pk=user_pk)
    credit_amount = request.POST.get('credit')
    client_object.credit_in+=float(credit_amount)
    client_object.save()
    return redirect('clientprofile',user_pk)

def change_client_logo(request,user_pk):
    client_object = Client.objects.get(pk=user_pk)
    logo = request.FILES['logo']
    client_object.logo = logo
    client_object.save()
    return redirect('clientprofile',user_pk)


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