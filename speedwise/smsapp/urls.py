from django.urls import path
from .models import *
from . import views
from django.views.generic.base import View
from .views import ClientView,DashboardView,ClientProfile,Operators

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('clients', ClientView.as_view(), name='clients'),
    path('clients/delete/<user_pk>', views.delete_user, name='deleteuser'),
    path('clients/edit/<user_pk>', views.edit_user, name='edituser'),
    path('clients/<user_pk>/profile', ClientProfile.as_view(), name='clientprofile'),
    path('clients/<user_pk>/addcredit', views.add_client_credit, name='addcredit'),
    path('clients/<user_pk>/changelogo', views.change_client_logo, name='changeclientlogo'),
    path('operators', Operators.as_view(), name='operators'),
]