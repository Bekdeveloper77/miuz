from django.contrib import admin
from .models import (Menu,Sciences,Applications,Groups,Edutype,Comissions, ExamResult)
# Register your models here.

# Register your models here.
admin.site.register(Menu)
admin.site.register(Sciences)
admin.site.register(Edutype)
admin.site.register(Groups)
admin.site.register(Comissions)

@admin.register(Applications)
class ApplicationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'mid_name',  'organization', 'number', 'date','status', 'user', 'score',)
    search_fields = ('last_name', 'organization', 'phone_number')
    list_filter = ('first_name','status',)
    list_editable = ('score',)

@admin.register(ExamResult)

class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('application', 'score', 'exam_date', 'exam_subject', 'passed')  # Ko'rsatadigan ustunlar
    search_fields = ('application__user__username',)  # Foydalanuvchi nomi orqali qidirish
    list_filter = ('passed',)  # O'tgan yoki o'tmagan bo'yicha filtr

    def save_model(self, request, obj, form, change):
        if obj.score is not None:
            obj.passed = obj.score >= 50  # Masalan, 50 dan yuqori ballni o'tgan deb hisoblash
        super().save_model(request, obj, form, change)

