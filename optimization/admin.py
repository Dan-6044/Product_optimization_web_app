from django.contrib import admin
from .models import Subscription, VisualizationData

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'amount', 'taxes', 'total_amount', 'subscription_date', 'expiration_date')
    list_filter = ('subscription_type', 'payment_method', 'is_company', 'subscription_date')
    search_fields = ('user__username', 'country', 'username')

admin.site.register(Subscription, SubscriptionAdmin)
from .models import OptimizationData

class OptimizationDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'upload_date', 'file')
    search_fields = ('user__username', 'file')

admin.site.register(OptimizationData, OptimizationDataAdmin)
admin.site.register(VisualizationData)