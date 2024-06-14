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

from .models import Pipeline, Custom, Upload, FileUpload, MetadataFormsField, FieldOption, MetadataValue, AllowedFileType, Note, UploadValidation
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.db.models import Q
from rest_flex_fields import FlexFieldsModelSerializer

class AllowedFileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedFileType
        fields = ['id', 'mime']

class FieldOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldOption
        fields = ['id', 'form_field', 'key', 'value', 'order', 'dflt']

class MetadataFormsFieldSerializer(serializers.ModelSerializer):
    options = FieldOptionSerializer(many=True, read_only=True)
    groupe_scope_name = serializers.SerializerMethodField("get_groupe_scope_name")
    class Meta:
        model = MetadataFormsField
        fields = ['id', 'pipeline', 'key', 'label', 'description', 'type', 'required', 'order', 'default_value', 'scope', 'options', 'groupe_scope_name']

    def get_groupe_scope_name(self, obj):
        if obj.scope:
            for q in Group.objects.all():
                if str(obj.scope) == str(q.id):
                    return q.description        
        return None

class PipelineFormsFieldsNoScopeSerializer(serializers.ModelSerializer):
    mimes = AllowedFileTypeSerializer(many=True, read_only=True)
    fields = serializers.SerializerMethodField("get_no_scope_fields")

    def get_no_scope_fields(self, obj):
        qs = MetadataFormsField.objects.filter(pipeline=obj, scope=None)
        serializer = MetadataFormsFieldSerializer(instance=qs, many=True)
        return serializer.data

    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'max_size_in_byte', 'default_same_metadata_for_each_file', 'can_edit_same_metadata_for_each_file', 'mimes', 'fields']

class PipelineSerializer(serializers.ModelSerializer):
    fields = MetadataFormsFieldSerializer(many=True, read_only=True)
    mimes = AllowedFileTypeSerializer(many=True, read_only=True)
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'max_size_in_byte', 'default_same_metadata_for_each_file', 'can_edit_same_metadata_for_each_file', 'mimes', 'fields']

class PipelineMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'fields', 'default_same_metadata_for_each_file', 'can_edit_same_metadata_for_each_file']

class CustomSerializer(serializers.ModelSerializer):
    pipeline = PipelineSerializer(many=False, read_only=True)
    class Meta:
        model = Custom
        fields = ['id', 'user', 'pipeline']
        lookup_field = "user"

class UserSerializer(serializers.ModelSerializer):
    custom = CustomSerializer(many=False, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'custom']

class GroupSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Group
        fields = '__all__'

class UserMinimalSerializer(serializers.ModelSerializer):
    pipeline = serializers.SerializerMethodField("get_pipeline")
    pipeline_name = serializers.SerializerMethodField("get_pipeline_name")
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'pipeline', 'groups', 'pipeline_name']

    def get_pipeline(self, obj):
        return obj.custom.pipeline.id if hasattr(obj, "custom") else None
    
    def get_pipeline_name(self, obj):
        return obj.custom.pipeline.name if hasattr(obj, "custom") else ""

class MetadataValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataValue
        fields = ['id', 'file', 'key', 'value']

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'note', 'upload', 'created', 'user']

class FileUploadSerializer(serializers.ModelSerializer):
    values = MetadataValueSerializer(many=True, read_only=True)
    size = serializers.SerializerMethodField("get_size")
    class Meta:
        model = FileUpload
        fields = ['id', 'upload', 'checksum', 'uploaded_file', 'name', 'size', 'type', 'values']
    
    def get_size(self, obj):
        return obj.uploaded_file.size if hasattr(obj, "uploaded_file") else None

class UploadSerializer(serializers.ModelSerializer):
    files = FileUploadSerializer(many=True, read_only=True)
    class Meta:
        model = Upload
        fields = ['id', 'uploaded_at', 'same_meta_for_each_file', 'status', 'files']
        read_only_fields = ['files']

class UploadMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ['id', 'uploaded_at', 'same_meta_for_each_file', 'files']

class UploadValidationSerializer(serializers.ModelSerializer):

    class Meta:
        model = UploadValidation
        fields = ['id', 'state', 'upload', 'workflow', 'group']


        
    
class UploadValidationForListSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = UploadValidation
        fields = ['id', 'state', 'upload', 'workflow', 'group']