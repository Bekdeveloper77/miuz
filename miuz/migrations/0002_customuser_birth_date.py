# Generated by Django 4.2.19 on 2025-02-15 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miuz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='birth_date',
            field=models.CharField(blank=True, max_length=14, null=True, unique=True),
        ),
    ]
