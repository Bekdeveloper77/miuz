from django.contrib import admin
from .models import (Menu,Sciences,Applications,Groups,Edutype,Comissions)
# Register your models here.

# Register your models here.
admin.site.register(Menu)
admin.site.register(Sciences)
admin.site.register(Edutype)
admin.site.register(Groups)
admin.site.register(Comissions)

@admin.register(Applications)
class ApplicationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'father_name',  'organization', 'number', 'date','status', 'user',)
    search_fields = ('last_name', 'organization', 'number')
    list_filter = ('first_name','status',)



