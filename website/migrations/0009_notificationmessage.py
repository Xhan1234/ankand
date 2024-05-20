# Generated by Django 5.0.2 on 2024-04-08 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_rename_state_deliverycharge_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=40)),
                ('message', models.TextField(max_length=1024, null=True)),
                ('status', models.BooleanField(choices=[(True, 'Active'), (False, 'Deactive')], default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
    ]
