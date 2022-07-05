from django.contrib import admin

from .models import *


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'name', 'main_currency', 'budget')
    list_display_links = ('pk', 'name')
    
    
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'exchange_to', 'exchange_rate', 'exchange_rate_reverse')
    list_display_links = ('pk', 'name')
    search_fields = ('name', 'exchange_to', 'exchange_rate_reverse')
    ordering = ['pk']
    

class WalletAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'name', 'balance', 'currency', 'is_archive')
    list_display_links = ('pk', 'name')
    
    
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'name', 'type_of', 'is_budget', 'budget_amount', 'is_archive')
    list_display_links = ('pk', 'name')
    
    
class OperationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'updated_at', 'from_wallet', 'category', 'to_wallet',
                    'currency1', 'amount1', 'currency2', 'amount2', 'description')
    list_display_links = ('pk', 'updated_at')
    
    
class DefaultCategoriesAdmin(admin.ModelAdmin):
    list_display = ('category_type_of', 'category_name')
    
    
class DefaultWalletsAdmin(admin.ModelAdmin):
    list_display = ('wallet_name',)
    

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Operation, OperationAdmin)

admin.site.register(DefaultCategories, DefaultCategoriesAdmin)
admin.site.register(DefaultWallets, DefaultWalletsAdmin)
