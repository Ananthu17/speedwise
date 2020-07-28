from django.urls import path
from .models import *
from . import views
from django.views.generic.base import View
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', views.logout_view, name='logout'),
    path('password_reset', auth_views.PasswordResetView.as_view(template_name='smsapp/password_reset_form.html'), name='password_reset'),
    path('password_reset/done', auth_views.PasswordResetDoneView.as_view(template_name='smsapp/password_reset_done.html'), name='password_reset_done'),
    path('password_reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='smsapp/password_change_form.html'), name='password_reset_confirm'),
    path('password_reset/complete', auth_views.PasswordResetCompleteView.as_view(template_name='smsapp/password_change_done.html'), name='password_reset_complete'),
    path('clients', ClientView.as_view(), name='clients'),
    path('clients/delete/<user_pk>', views.delete_user, name='deleteuser'),
    path('clients/<user_pk>/profile', ClientProfile.as_view(), name='clientprofile'),
    path('clients/<user_pk>/addcredit', views.add_client_credit, name='addcredit'),
    path('clients/<user_pk>/removecredit', views.remove_client_credit, name='removecredit'),
    path('clients/<user_pk>/setclientcredit', views.set_client_credit_limit, name='setclientcredit'),
    path('clients/<user_pk>/changeclientlogo', views.change_client_logo, name='changeclientlogo'),
    path('clients/<user_pk>/allowed_countries', views.allowed_countries_for_clients, name='allowedcountriesforclients'),
    path('clients_sub_users', ClientSubUserView.as_view(), name='clients_sub_users'),
    path('operators', Operators.as_view(), name='operators'),
    path('operators/delete/<operator_pk>', views.delete_operator, name='deleteoperator'),
    path('contacts', Contacts_View.as_view(), name='contacts'),
    path('contacts/delete/<contact_pk>', views.delete_contact, name='deletecontact'),
    path('contacts/import', views.import_contacts, name='importcontact'),
    path('messaging', Messages_View.as_view(), name='messaging'),
    path('messaging/delete/<message_pk>', views.delete_message, name='deletemessage'),
    path('templates', Templates_View.as_view(), name='templates'),
    path('countries', Country_View.as_view(), name='countries'),
    path('countries/delete/<country_pk>', views.delete_country, name='deletecountry'),
    path('message-response', MessageResposeView.as_view(), name='message-response'),
    path('reports',ReportsView.as_view(),name="reports")
]
