from django.db import models
from django.core.validators import RegexValidator
#from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

# Create your models here
# admin

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    mid_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Otasining ismi")
    pin = models.CharField(max_length=14, unique=True, null=True, blank=True)
    birth_date = models.CharField(max_length=14, unique=True, null=True, blank=True)


    def __str__(self):
        return f"{self.username} {self.first_name} {self.last_name} {self.mid_name}"

class Menu(models.Model):
    name = models.CharField(max_length=100, verbose_name='Menu nomi')
    order = models.CharField(max_length=100, verbose_name='Tartib raqami')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Menu'
        verbose_name_plural = 'Menu'


class Comissions(models.Model):
    chairman = models.CharField(max_length=100, verbose_name='Komissiya raisi')
    deputy = models.CharField(max_length=100, verbose_name='Rais orinbosari')
    secretary = models.CharField(max_length=100, verbose_name='Komissiya kotibi')
    members = models.CharField(max_length=100, verbose_name='Komissiya azolari')

    def __str__(self):
        return self.chairman

    class Meta:
        verbose_name = 'Comissions'
        verbose_name_plural = 'Comissions'


class Groups(models.Model):
    datetime = models.DateTimeField(auto_now=True, verbose_name="Vaqti")
    directions = models.CharField(max_length=500, verbose_name="Yonalish nomi")
    comission = models.ForeignKey(Comissions, on_delete=models.CASCADE, verbose_name="Komissiya")

    def __str__(self):
        return self.directions  # Yonalish nomini qaytarish

    class Meta:
        verbose_name = 'Groups'
        verbose_name_plural = 'Groups'

class Sciences(models.Model):
    name = models.CharField(max_length=100, verbose_name="Fan nomi")
    directions = models.ForeignKey(Groups, on_delete=models.CASCADE, verbose_name="Yonalish nomi")
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Fan nomi'
        verbose_name_plural = 'Fan nomi'


class Edutype(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nomi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Talim turi'
        verbose_name_plural = 'Talim turi'


class Applications(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilingan'),
        ('rejected', 'Rad etilgan'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # talabgor
    first_name = models.CharField(max_length=100, verbose_name="Ism")  # Ism
    last_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Familiya")  # Familiya
    mid_name = models.CharField(max_length=100, verbose_name="Otasining_ismi")  # Otasining ismi
    directions = models.ForeignKey(Groups, on_delete=models.CASCADE, related_name="applications",
                                   verbose_name="Ixtisoslik")  # Ixtisoslik nomi
    sciences = models.ForeignKey(Sciences, on_delete=models.CASCADE, related_name="applications",
                                 verbose_name="Fan")  # Malakaviy imtihon fani
    type_edu = models.ForeignKey(Edutype, on_delete=models.CASCADE, related_name="applications",
                                 verbose_name="Talim turi")  # Ta'lim turi
    organization = models.CharField(max_length=100, verbose_name="Tashkilot_nomi")  # Tashkilot nomi
    number = models.CharField(max_length=13, verbose_name="Telefon raqami")  # Telefon raqam
    oak_decision = models.FileField(upload_to='oak_decision/', blank=True, null=True,
                                    verbose_name="OAK byulleteni yoki tashkilot kengashi qarori", )  # OAK hujjati
    work_order = models.FileField(upload_to='work_order/', blank=True, null=True,
                                  verbose_name="Ish_buyrugi")  # Ish buyrug‘i
    reference_letter = models.FileField(upload_to='reference_letter/', blank=True, null=True,
                                        verbose_name="Yollanma_xati")  # Holati
    application = models.FileField(upload_to='application/', verbose_name="Arizasi")  # Arizasi
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Ariza holati
    reason = models.TextField(null=True, blank=True)  # Rad etish sababi
    date = models.DateTimeField(auto_now=True, verbose_name="Ariza yuborilgan vaqti")
    created_at = models.DateTimeField(auto_now_add=True)  # Yangi maydon qo'shildi
    score = models.IntegerField(default=0, verbose_name="ball")
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        ordering = ['-created_at']  # Oxirgi qo'shilganini birinchi qilib tartiblang
        verbose_name = 'Applications'
        verbose_name_plural = 'Applications'


class ExamResult(models.Model):
    application = models.ForeignKey(Applications, on_delete=models.CASCADE, related_name='Ariza')
    score = models.IntegerField(null=True, blank=True)
    exam_date = models.DateField()
    exam_subject = models.CharField(max_length=255)
    passed = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.application} - {self.exam_subject} - {self.score}"
    class Meta:
        verbose_name = 'ExamResult'
        verbose_name_plural = 'ExamResult'



class Curriculum(models.Model):
    directions_name = models.CharField(max_length=1000, verbose_name="Oqov_dasturi_nomi")
    direct_file = models.FileField(upload_to='directions/', blank=True, null=True,
                                  verbose_name="Oqov_dasturi")

    def __str__(self):
        return f"{self.directions_name}"

    class Meta:
        verbose_name = 'Curriculum'
        verbose_name_plural = 'Curriculum'
   
 