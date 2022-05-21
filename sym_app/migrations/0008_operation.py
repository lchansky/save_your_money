# Generated by Django 4.0.4 on 2022-05-05 11:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sym_app', '0007_alter_category_budget_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(verbose_name='Дата и время операции')),
                ('amount1', models.FloatField(verbose_name='Сумма списания')),
                ('amount2', models.FloatField(verbose_name='Сумма платежа')),
                ('description', models.CharField(max_length=150, verbose_name='Описание операции')),
                ('category_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sym_app.category', verbose_name='ID категории')),
                ('currency1', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='currency1', to='sym_app.currency', verbose_name='ID валюты списания')),
                ('currency2', models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.PROTECT, related_name='currency2', to='sym_app.currency', verbose_name='ID валюты платежа')),
                ('from_wallet_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sym_app.wallet', verbose_name='ID счёта списания')),
                ('to_wallet_id', models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, related_name='to_wallet', to='sym_app.wallet', verbose_name='ID счёта получения')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
        ),
    ]