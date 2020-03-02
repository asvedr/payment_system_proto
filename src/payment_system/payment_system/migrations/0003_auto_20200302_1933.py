# Generated by Django 2.2.4 on 2020-03-02 19:33

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payment_system', '0002_paymenttransaction_spent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='type',
            field=models.TextField(choices=[('user_account', 'User account'), ('taxes_account', 'Taxes account')], db_index=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='slug',
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name='paymenttransaction',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='paymenttransaction',
            name='processed_at',
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='account',
            unique_together={('user', 'currency')},
        ),
        migrations.AddConstraint(
            model_name='account',
            constraint=models.CheckConstraint(check=models.Q(amount__gte=0), name='amount_gte_0'),
        ),
    ]
