# Generated by Django 4.0.4 on 2022-05-05 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sym_app', '0008_operation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='from_wallet_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_wallet', to='sym_app.wallet', verbose_name='ID счёта списания'),
        ),
    ]