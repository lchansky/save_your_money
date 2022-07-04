# Generated by Django 4.0.4 on 2022-05-05 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sym_app', '0010_alter_operation_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='to_wallet_id',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, related_name='to_wallet', to='sym_app.wallet', verbose_name='ID счёта получения'),
        ),
    ]