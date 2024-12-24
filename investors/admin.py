from django.contrib import admin
from .models import InversorTemporal
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class InversorTemporalResourseces(resources.ModelResource):
    class Meta:
        model = InversorTemporal
        

class InversorTemporalAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('last_name', 'last_name', 'email')
    search_fields = ['first_name','last_name', 'email']
    resource_class = InversorTemporalResourseces
    
admin.site.register(InversorTemporal, InversorTemporalAdmin)