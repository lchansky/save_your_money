# Generated by Django 4.0.4 on 2022-06-03 10:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sym_app', '0029_alter_operation_exchange_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='amount2',
            field=models.FloatField(verbose_name='Сумма платежа'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='currency1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='currency1', to='sym_app.currency', verbose_name='Валюта'),
        ),
    ]
