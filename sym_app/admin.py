from django.contrib import admin

from .models import *


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'exchange_to', 'exchange_rate')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'exchange_to')
    

admin.site.register(Currency, CurrencyAdmin)
