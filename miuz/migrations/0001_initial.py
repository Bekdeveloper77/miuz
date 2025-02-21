# Generated by Django 5.1.6 on 2025-02-15 10:29

import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comissions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chairman', models.CharField(max_length=100, verbose_name='Komissiya raisi')),
                ('deputy', models.CharField(max_length=100, verbose_name='Rais orinbosari')),
                ('secretary', models.CharField(max_length=100, verbose_name='Komissiya kotibi')),
                ('members', models.CharField(max_length=100, verbose_name='Komissiya azolari')),
            ],
            options={
                'verbose_name': 'Comissions',
                'verbose_name_plural': 'Comissions',
            },
        ),
        migrations.CreateModel(
            name='Curriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('directions_name', models.CharField(max_length=1000, verbose_name='Oqov_dasturi_nomi')),
                ('direct_file', models.FileField(blank=True, null=True, upload_to='directions/', verbose_name='Oqov_dasturi')),
            ],
            options={
                'verbose_name': 'Curriculum',
                'verbose_name_plural': 'Curriculum',
            },
        ),
        migrations.CreateModel(
            name='Edutype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nomi')),
            ],
            options={
                'verbose_name': 'Talim turi',
                'verbose_name_plural': 'Talim turi',
            },
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Menu nomi')),
                ('order', models.CharField(max_length=100, verbose_name='Tartib raqami')),
            ],
            options={
                'verbose_name': 'Menu',
                'verbose_name_plural': 'Menu',
            },
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('mid_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Otasining ismi')),
                ('pin', models.CharField(blank=True, max_length=14, null=True, unique=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Applications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='Ism')),
                ('last_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Familiya')),
                ('mid_name', models.CharField(max_length=100, verbose_name='Otasining_ismi')),
                ('organization', models.CharField(max_length=100, verbose_name='Tashkilot_nomi')),
                ('number', models.CharField(max_length=13, verbose_name='Telefon raqami')),
                ('oak_decision', models.FileField(blank=True, null=True, upload_to='oak_decision/', verbose_name='OAK byulleteni yoki tashkilot kengashi qarori')),
                ('work_order', models.FileField(blank=True, null=True, upload_to='work_order/', verbose_name='Ish_buyrugi')),
                ('reference_letter', models.FileField(blank=True, null=True, upload_to='reference_letter/', verbose_name='Yollanma_xati')),
                ('application', models.FileField(upload_to='application/', verbose_name='Arizasi')),
                ('status', models.CharField(choices=[('pending', 'Kutilmoqda'), ('accepted', 'Qabul qilingan'), ('rejected', 'Rad etilgan')], default='pending', max_length=20)),
                ('reason', models.TextField(blank=True, null=True)),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Ariza yuborilgan vaqti')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('score', models.IntegerField(default=0, verbose_name='ball')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('type_edu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='miuz.edutype', verbose_name='Talim turi')),
            ],
            options={
                'verbose_name': 'Applications',
                'verbose_name_plural': 'Applications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExamResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('exam_date', models.DateField()),
                ('exam_subject', models.CharField(max_length=255)),
                ('passed', models.CharField(max_length=255)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Ariza', to='miuz.applications')),
            ],
            options={
                'verbose_name': 'ExamResult',
                'verbose_name_plural': 'ExamResult',
            },
        ),
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now=True, verbose_name='Vaqti')),
                ('directions', models.CharField(max_length=500, verbose_name='Yonalish nomi')),
                ('comission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='miuz.comissions', verbose_name='Komissiya')),
            ],
            options={
                'verbose_name': 'Groups',
                'verbose_name_plural': 'Groups',
            },
        ),
        migrations.AddField(
            model_name='applications',
            name='directions',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='miuz.groups', verbose_name='Ixtisoslik'),
        ),
        migrations.CreateModel(
            name='Sciences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Fan nomi')),
                ('directions', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='miuz.groups', verbose_name='Yonalish nomi')),
            ],
            options={
                'verbose_name': 'Fan nomi',
                'verbose_name_plural': 'Fan nomi',
            },
        ),
        migrations.AddField(
            model_name='applications',
            name='sciences',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='miuz.sciences', verbose_name='Fan'),
        ),
    ]
