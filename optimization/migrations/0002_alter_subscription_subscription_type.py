# Generated by Django 5.1.1 on 2024-10-05 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('optimization', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='subscription_type',
            field=models.CharField(choices=[('Free Tier ', 'Free Tier'), ('Monthly Plan', 'Monthly Subscription'), ('Yearly Plan', 'Yearly Subscription')], max_length=16),
        ),
    ]
