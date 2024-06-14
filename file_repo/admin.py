"""
Copyright (c) BCU Fribourg

This file is part of eUploader.
eUploader is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by the 
Free Software Foundation, either version 3 of the License, or (at your option) any later version.
eUploader is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with eUploader. 
If not, see <https://www.gnu.org/licenses/>.
"""

from django.contrib import admin
from django.conf import settings

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.http import HttpResponse
import os, io
import zipfile
import datetime
from .models import FileUpload, AllowedFileType, Config, Pipeline, MetadataFormsField, Custom, MetadataValue, Upload, FieldOption, Workflow, UploadValidation, Note
from nested_inline.admin import NestedModelAdmin, NestedTabularInline


from modeltranslation.admin import TranslationAdmin

def download_multiple_files(FileUploadAdmin, request, queryset):
    date = datetime.datetime.now().strftime("%d%m%Y-%H%M%S")
    zip_subdir = f"eUploader_DL_{date}"
    zip_filename = zip_subdir + ".zip"
    byte_stream = io.BytesIO()
    zf = zipfile.ZipFile(byte_stream, "w")

    for file in queryset:
        zip_path = os.path.join(zip_subdir, file.uploaded_file.name)
        zf.write(os.path.join(settings.MEDIA_ROOT, file.uploaded_file.name), zip_path)

    zf.close()
    response = HttpResponse(byte_stream.getvalue(), content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return response        
download_multiple_files.short_description = "Télécharger le(s) fichier(s) sélectionné(s)"

class MetadataValueInline(NestedTabularInline):
    model = MetadataValue
    extra = 1

class FileUploadInline(NestedTabularInline):
    model = FileUpload
    inlines = [MetadataValueInline]
    extra = 1

@admin.register(Upload)
class UploadAdmin(NestedModelAdmin):
    search_fields = ['uploaded_at', 'user__username', 'pipeline']
    ordering = ['uploaded_at', 'pipeline']
    list_display = ['id', 'user', 'uploaded_at','files_count', 'status', 'pipeline']
    list_filter = ['uploaded_at', 'status', 'pipeline']

    inlines = [
        FileUploadInline
    ]

    def files_count(self, obj):
        return obj.files.count()

@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    search_fields = ['uploaded_file', 'upload__user__username']
    list_display = ['id', 'pipeline', 'user', 'checksum', 'name', 'uploaded_file', 'type']
    list_filter = ['upload__pipeline__name', 'upload__user__username']
    actions = [download_multiple_files]

    inlines = [
        MetadataValueInline,
    ]

    def user(self, obj):
        return User.objects.get(id=obj.upload.user.id)

    def pipeline(self, obj):
        return obj.upload.pipeline

    def get_action_choices(self, request):
        choices = super(FileUploadAdmin, self).get_action_choices(request)
        choices = list(reversed(choices))
        for i, choice in enumerate(choices):
            if choice[0] == '':
                choices.pop(i)
        return choices

@admin.register(AllowedFileType)
class AllowedFileTypeAdmin(admin.ModelAdmin):
    search_fields = ['mime']

class AllowedFileTypeInline(admin.TabularInline):
    model = Pipeline.mimes.through
    extra = 1

@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    search_fields = ['key', 'value']
    list_display = ['key', 'value']

@admin.register(FieldOption)
class FieldOptionAdmin(TranslationAdmin):
    search_fields = ['key', 'value', 'form_field', 'order', 'dflt']
    list_display = ['key', 'value', 'form_field', 'order', 'dflt', 'pipeline']
    list_filter = ['form_field__pipeline']

    def pipeline(self, obj):
        return obj.form_field.pipeline

class FieldOptionInline(NestedTabularInline):
    model = FieldOption
    extra = 3

@admin.register(MetadataFormsField)
class MetadataFormsFieldAdmin(TranslationAdmin):
    search_fields = ['key', 'label', 'description', 'type', 'required', 'order']
    list_display = ['key', 'label', 'description', 'type', 'required', 'order', 'default_value', 'pipeline']
    list_filter = ['pipeline']
    inlines = [FieldOptionInline]

    def pipeline(self, obj):
        return obj.pipeline

class MetadataFormsFieldInline(admin.TabularInline):
    model = MetadataFormsField
    inlines = [FieldOptionInline]
    fields = ('key', 'type', 'required', 'order', 'default_value', 'scope')
    extra = 1
    show_change_link = True

@admin.register(Pipeline)
class PipelineAdmin(TranslationAdmin):
    search_fields = ['name', 'description', 'max_size_in_byte', 'default_same_metadata_for_each_file', 'can_edit_same_metadata_for_each_file']
    list_display = ['name', 'description', 'max_size_in_byte', 'get_mimes', 'default_same_metadata_for_each_file', 'can_edit_same_metadata_for_each_file']
    fields = ['name', 'description', 'max_size_in_byte', 'default_same_metadata_for_each_file', 'can_edit_same_metadata_for_each_file']
    filter_horizontal = ('mimes',)
    inlines = [
        AllowedFileTypeInline,
        MetadataFormsFieldInline
    ]

    def get_mimes(self, obj):
        return [mime for mime in obj.mimes.all()]

class CustomInline(admin.TabularInline):
    model = Custom

class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ('pipeline',)
    search_fields = BaseUserAdmin.list_display + ('pipeline',)

    inlines = (CustomInline, )

    def pipeline(self, obj):
        return  Pipeline.objects.get(id=obj.custom.pipeline.id) if (hasattr(obj, "custom") and hasattr(obj.custom.pipeline, "id")) else None
    
class GroupAdmin(BaseGroupAdmin):
    list_display = BaseGroupAdmin.list_display + ('description',)
    search_fields = BaseGroupAdmin.list_display + ('description',)

@admin.register(MetadataValue)
class MetadataValueAdmin(admin.ModelAdmin):
    search_fields = ['key', 'value']
    list_display = ['key', 'value']

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_display = ['name', 'description']

@admin.register(UploadValidation)
class UploadValidationAdmin(admin.ModelAdmin):
    search_fields = ['id', 'state', 'upload', 'upload_id', 'validated_by']
    list_display = ['id', 'state', 'upload', 'upload_id', 'validated_by']

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    search_fields = ['note', 'upload', 'created', 'user']
    list_display = ['note', 'upload', 'created', 'user']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)