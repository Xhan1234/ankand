# Generated by Django 5.0.2 on 2024-03-24 09:13

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_alter_slider_image_alter_slider_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('email', models.CharField(max_length=25)),
                ('phone', models.CharField(max_length=255, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numerics are allowed.')])),
                ('subject', models.CharField(max_length=255)),
                ('message', models.TextField(max_length=1024, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
