# Generated by Django 4.0.4 on 2022-05-16 07:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sym_app', '0015_alter_wallet_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='category_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sym_app.category', verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='currency1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='currency1', to='sym_app.currency', verbose_name='Валюта списания'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='currency2',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.PROTECT, related_name='currency2', to='sym_app.currency', verbose_name='Валюта платежа'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='from_wallet_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_wallet', to='sym_app.wallet', verbose_name='Счёт списания'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='to_wallet_id',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='to_wallet', to='sym_app.wallet', verbose_name='Счёт получения'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
