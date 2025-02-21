from django.contrib import admin
from .models import (Menu,Sciences,Applications,Groups,Edutype,Comissions, ExamResult,Curriculum)
# Register your models here.

# Register your models here.
admin.site.register(Menu)
admin.site.register(Sciences)
admin.site.register(Edutype)
admin.site.register(Groups)
admin.site.register(Comissions)
admin.site.register(Curriculum)

@admin.register(Applications)
class ApplicationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'mid_name',  'organization', 'number', 'date','status', 'user', 'score',)
    search_fields = ('last_name', 'organization', 'phone_number')
    list_filter = ('first_name','status',)
    list_editable = ('score',)

@admin.register(ExamResult)

class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('application', 'score', 'exam_date',)  # Ko'rsatadigan ustunlar
    search_fields = ('application__user__username',)  # Foydalanuvchi nomi orqali qidirish
   

    

