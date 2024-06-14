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

from django.db import models
from django.utils import timezone, dateformat
from django.contrib.auth.models import User, Group
import os
from .apps import FileRepoConfig
from django_clamd.validators import validate_file_infection

Group.add_to_class('description', models.TextField(null=True, blank=True))

def user_directory_path(instance, filename):
    pipeline_path = ""
    if hasattr(instance.upload.user, "custom"):
        pipeline_path = instance.upload.user.custom.pipeline
    else:
        pipeline_path = "no_pipeline"
    
    # file will be uploaded to MEDIA_ROOT/user_<id>/upload_<id>/<filename>
    return '{0}/{1}/{2}/{3}'.format(pipeline_path, instance.upload.user, instance.upload.id, filename)


class Config(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(null=False, blank=False, max_length=255, unique=True)
    value = models.CharField(null=False, blank=False, max_length=255)

    def __str__(self):
        return self.key

class Pipeline(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(null=False, blank=False, max_length=255, unique=True)
    description = models.TextField(null=False, blank=False)
    default_same_metadata_for_each_file = models.BooleanField(default=True)
    can_edit_same_metadata_for_each_file = models.BooleanField(default=True)
    max_size_in_byte = models.IntegerField(default=FileRepoConfig.DEFAULT_SIZE_LIMIT_IN_BYTE)

    def __str__(self):
        return self.name
    
class Upload(models.Model):

    class Status(models.TextChoices):
        INIT = 'INIT', 'INIT'
        FILE_UPLOADED = 'FILE_UPLOADED', 'FILE_UPLOADED'
        COMPLETED ='COMPLETED', 'COMPLETED'
        ERROR = 'ERROR', 'ERROR'
        ABORTED = 'ABORTED', 'ABORTED'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    pipeline = models.ForeignKey(Pipeline, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    same_meta_for_each_file = models.BooleanField(default=True)
    status = models.CharField(
        max_length=13,
        choices=Status.choices,
        default=Status.INIT,
    )

    def __str__(self):
        return f"{self.user} {self.uploaded_at}"
    
class FileUpload(models.Model):
    id = models.AutoField(primary_key=True)
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name="files")
    uploaded_file = models.FileField(null=False, blank=False, upload_to=user_directory_path) # use this to test without antivirus
    # uploaded_file = models.FileField(validators=[validate_file_infection], null=False, blank=False, upload_to=user_directory_path)
    checksum = models.CharField(null=True, blank=True, max_length=255)
    type = models.CharField(null=True, blank=True, max_length=255, verbose_name="file type from frontend")
    
    def name(self):
        return os.path.basename(self.uploaded_file.name)

    def __str__(self):
        return self.uploaded_file.name

# Custom user class using django base user class
class Custom(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    pipeline = models.ForeignKey(Pipeline, blank=True, null=True, default=None, on_delete=models.DO_NOTHING)

class AllowedFileType(models.Model):
    id = models.AutoField(primary_key=True)
    mime = models.CharField(null=False, blank=False, max_length=255)
    pipeline = models.ManyToManyField(Pipeline, blank=True, related_name="mimes")

    def __str__(self):
        return self.mime

class MetadataFormsField(models.Model):

    class Type(models.TextChoices):
        TEXT = 'TEXT', 'text'
        CHECKBOX ='CHECKBOX', 'checkbox'
        NUMBER = 'NUMBER', 'number'
        DATE = 'DATE', 'date',
        TEXT_AREA = 'TEXT_AREA', 'text_area',
        SELECT = 'SELECT', 'select',
        TIME = 'TIME', 'time',
        DURATION = 'DURATION', 'duration'

    id = models.AutoField(primary_key=True)
    pipeline = models.ForeignKey(Pipeline, default=None, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(null=True, blank=True, max_length=255)
    description = models.TextField(null=True, blank=True)
    key = models.CharField(null=False, blank=False, max_length=255)
    type = models.CharField(max_length=255, choices=Type.choices, default = Type.TEXT, null=True, blank=True)
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    scope = models.ForeignKey(Group, null=True, blank=True, default=None, on_delete=models.CASCADE)
    default_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.key
    
    class Meta:
        ordering = ['scope', 'order']
        constraints = [
            models.UniqueConstraint(fields=['key', 'pipeline'], name="key_per_pipeline"),
        ]

class FieldOption(models.Model):
    id = models.AutoField(primary_key=True)
    form_field = models.ForeignKey(MetadataFormsField, default=None, on_delete=models.CASCADE, related_name="options")
    key = models.CharField(null=False, blank=False, max_length=255)
    value = models.CharField(null=False, blank=False, max_length=255)
    order = models.IntegerField(default=0)
    dflt = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.form_field.pipeline}: {self.form_field}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['form_field', 'key'], name="key_per_form_field"),
        ]


class MetadataValue(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.ForeignKey(FileUpload, default=None, on_delete=models.CASCADE, related_name="values")
    key = models.CharField(null=False, blank=False, max_length=255)
    value = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.key


class Workflow(models.Model):

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    pipeline = models.ForeignKey(Pipeline, blank=True, null=True, on_delete=models.SET_NULL, related_name="workflows")
    validator_groups = models.ManyToManyField(Group)

    def __str__(self):
        return self.name



class UploadValidation(models.Model):

    class State(models.TextChoices):
        NOT_VALIDATED = 'NOT_VALIDATED', 'not_validated'
        VALIDATED_OK = 'VALIDATED_OK', 'validated_ok'
        VALIDATED_NOK = 'VALIDATED_NOK', 'validated_nok'

    id = models.AutoField(primary_key=True)
    state = models.CharField(max_length=255, choices=State.choices, default = State.NOT_VALIDATED, null=True, blank=True)
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name="validations")
    workflow = models.ForeignKey(Workflow, null=True, blank=True, on_delete=models.CASCADE, related_name="upload_validations")
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)
    validated_by = models.CharField(max_length=255, null=True, blank=True)

class Note(models.Model):
    id = models.AutoField(primary_key=True)
    note = models.TextField(null=True, blank=True)
    upload = models.ForeignKey(Upload, blank=True, null=True, on_delete=models.CASCADE, related_name="notes")
    created = models.DateTimeField(auto_now=True)
    user = models.CharField(null=False, blank=False, max_length=255)

    def __str__(self):
        return self.note
