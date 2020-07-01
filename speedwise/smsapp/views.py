from django.shortcuts import render
from django.views.generic import TemplateView
from .models import *

# Create your views here.

class ClientView(TemplateView):
    template_name = 'smsapp/clients.html'

    def get_context_data(self, **kwargs):
        context = super(ClientView, self).get_context_data(**kwargs)
        client_objects = Client.objects.all()
        context['clients'] = client_objects
        return context