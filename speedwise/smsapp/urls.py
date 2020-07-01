from django.urls import path
from .models import *
from . import views
from django.views.generic.base import View
from .views import ClientView

urlpatterns = [
    # path('', views.action_form_history_form,name="dashbord"),
    path('clients', ClientView.as_view(), name='clients')
]