from django.urls import path
from .models import *
from . import views
from django.views.generic.base import View
from .views import ClientView,DashboardView,ClientProfile,Operators,OperatorProfile,Contacts_View,ContactProfile,Messages_View,MessageProfile

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('clients', ClientView.as_view(), name='clients'),
    path('clients/delete/<user_pk>', views.delete_user, name='deleteuser'),
    path('clients/edit/<user_pk>', views.edit_user, name='edituser'),
    path('clients/<user_pk>/profile', ClientProfile.as_view(), name='clientprofile'),
    path('clients/<user_pk>/addcredit', views.add_client_credit, name='addcredit'),
    path('clients/<user_pk>/removecredit', views.remove_client_credit, name='removecredit'),
    path('clients/<user_pk>/changelogo', views.change_client_logo, name='changeclientlogo'),
    path('operators', Operators.as_view(), name='operators'),
    path('operators/<operator_pk>/profile', OperatorProfile.as_view(), name='operatorprofile'),
    path('operators/delete/<operator_pk>', views.delete_operator, name='deleteoperator'),
    path('operators/edit/<operator_pk>', views.edit_operator, name='editoperator'),
    path('contacts', Contacts_View.as_view(), name='contacts'),
    path('contacts/<contact_pk>/profile', ContactProfile.as_view(), name='contactprofile'),
    path('contacts/delete/<contact_pk>', views.delete_contact, name='deletecontact'),
    path('contacts/edit/<contact_pk>', views.edit_contact, name='editcontact'),
    path('messaging', Messages_View.as_view(), name='messaging'),
    path('messaging/<message_pk>/profile', MessageProfile.as_view(), name='messageprofile'),
    path('messaging/delete/<message_pk>', views.delete_message, name='deletemessage'),
    path('messaging/edit/<message_pk>', views.edit_message, name='editmessage'),
]