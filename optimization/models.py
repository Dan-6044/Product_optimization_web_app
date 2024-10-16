from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subscription(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('creditCard', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
    ]

    SUBSCRIPTION_TYPE_CHOICES = [
        ('Free Tier ', 'Free Tier'),
        ('Monthly Plan', 'Monthly Subscription'),
        ('Yearly Plan', 'Yearly Subscription'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    is_company = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    expiry_date = models.CharField(max_length=5, blank=True, null=True)  # MM/YY format
    cvv = models.CharField(max_length=4, blank=True, null=True)
    subscription_type = models.CharField(max_length=16, choices=SUBSCRIPTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=5, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    subscription_date = models.DateTimeField(default=timezone.now)
    expiration_date = models.DateField()

    def __str__(self):
        return f'{self.user.username} - {self.subscription_type}'

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'


class OptimizationData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.upload_date.strftime('%Y-%m-%d')}"

class VisualizationData(models.Model):
    optimization_data = models.ForeignKey(OptimizationData, on_delete=models.CASCADE, related_name='visualization')
    chart_type = models.CharField(max_length=20)
    data = models.JSONField()  # Store the processed data as JSON

    def __str__(self):
        return f"{self.optimization_data.user.username} - {self.chart_type}"
