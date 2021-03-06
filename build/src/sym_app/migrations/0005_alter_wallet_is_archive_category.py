# Generated by Django 4.0.4 on 2022-05-05 09:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sym_app', '0004_wallet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallet',
            name='is_archive',
            field=models.BooleanField(blank=True, default=False, verbose_name='Архивный счёт?'),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Название категории')),
                ('type_of', models.CharField(max_length=10, verbose_name='Тип категории')),
                ('is_budget', models.BooleanField(blank=True, default=False, verbose_name='Бюджет вкл./выкл.')),
                ('budget_amount', models.FloatField(blank=True, verbose_name='Размер бюджета')),
                ('is_archive', models.BooleanField(blank=True, default=False, verbose_name='Архивная категория?')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
        ),
    ]
