from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
# Register your models here.

admin.site.register(Operator)
admin.site.register(Client)
admin.site.register(ClientSubUser)
admin.site.register(Contact)
admin.site.register(Messages)
admin.site.register(Templates)
admin.site.register(Country)
admin.site.register(Notifications)
admin.site.register(WebhookResponse)