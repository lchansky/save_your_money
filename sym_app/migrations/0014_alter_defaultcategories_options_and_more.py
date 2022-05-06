# Generated by Django 4.0.4 on 2022-05-05 14:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sym_app', '0013_defaultcategories_defaultwallets_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='defaultcategories',
            options={'ordering': ['category_type_of', 'pk'], 'verbose_name': 'Дефолтные категории', 'verbose_name_plural': 'Дефолтные категории'},
        ),
        migrations.AlterModelOptions(
            name='defaultwallets',
            options={'ordering': ['wallet_name', 'pk'], 'verbose_name': 'Дефолтные счета', 'verbose_name_plural': 'Дефолтные счета'},
        ),
        migrations.AlterField(
            model_name='category',
            name='user',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='defaultcategories',
            name='category_name',
            field=models.CharField(max_length=150, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='defaultcategories',
            name='category_type_of',
            field=models.CharField(max_length=10, verbose_name='Тип'),
        ),
        migrations.AlterField(
            model_name='defaultwallets',
            name='wallet_name',
            field=models.CharField(max_length=150, verbose_name='Название'),
        ),
    ]
