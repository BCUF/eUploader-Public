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

from .models import Pipeline, Custom, Upload, FileUpload, MetadataFormsField, FieldOption, MetadataValue, AllowedFileType, Note, UploadValidation, Workflow
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from rest_flex_fields import FlexFieldsModelSerializer

class AllowedFileTypeSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = AllowedFileType
        fields = ['id', 'mime']

class FieldOptionSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = FieldOption
        fields = ['id', 'form_field', 'key', 'value', 'order', 'dflt']

class MetadataFormsFieldSerializer(FlexFieldsModelSerializer):
    options = FieldOptionSerializer(many=True, read_only=True)
    class Meta:
        model = MetadataFormsField
        fields = ['id', 'pipeline', 'key', 'label', 'description', 'type', 'required', 'order', 'scope', 'options']

class PipelineFormsFieldsNoScopeSerializer(FlexFieldsModelSerializer):
    mimes = AllowedFileTypeSerializer(many=True, read_only=True)
    # fields = serializers.SerializerMethodField("get_no_scope_fields")

    def get_no_scope_fields(self, obj):
        qs = MetadataFormsField.objects.filter(pipeline=obj, scope=None)
        serializer = MetadataFormsFieldSerializer(instance=qs, many=True)
        return serializer.data

    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'max_size_in_byte', 'mimes', 'fields']

class PipelineSerializer(FlexFieldsModelSerializer):
    fields = MetadataFormsFieldSerializer(many=True, read_only=True)
    mimes = AllowedFileTypeSerializer(many=True, read_only=True)
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'max_size_in_byte', 'mimes', 'fields']

class PipelineMinimalSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'name']

class CustomSerializer(FlexFieldsModelSerializer):
    pipeline = PipelineSerializer(many=False, read_only=True)
    class Meta:
        model = Custom
        fields = ['id', 'user', 'pipeline']
        lookup_field = "user"

class UserSerializer(FlexFieldsModelSerializer):
    # custom = CustomSerializer(many=False, read_only=True)
    class Meta:
        model = User
        # fields = '__all__'
        fields = ['id', 'username', 'email', 'custom']

class UserMinimalSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username']

class MetadataValueSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = MetadataValue
        fields = ['id', 'file', 'key', 'value']

class NoteSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'note', 'validation', 'created', 'user']

class FileUploadSerializer(FlexFieldsModelSerializer):
    values = MetadataValueSerializer(many=True, read_only=True)
    class Meta:
        model = FileUpload
        fields = ['id', 'upload', 'checksum', 'uploaded_file', 'name', 'type', 'values']
    
    def get_size(self, obj):
        return obj.uploaded_file.size if hasattr(obj, "uploaded_file") else None

class UploadSerializer(FlexFieldsModelSerializer):
    files = FileUploadSerializer(many=True, read_only=True)
    file_count = serializers.SerializerMethodField("get_file_count")
    class Meta:
        model = Upload
        
        fields = '__all__'
        # fields = ['id', 'uploaded_at', 'same_meta_for_each_file', 'status', 'files']
        read_only_fields = ['files']
        expandable_fields = {
            'user': UserMinimalSerializer,
        }
    def get_file_count(self, obj):
        return len(obj.files.all())

class UploadMinimalSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Upload
        fields = ['id', 'uploaded_at', 'same_meta_for_each_file', 'files']

class UploadValidationSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = UploadValidation
        fields = ['id', 'state', 'upload', 'workflow', 'group']

class GroupSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'description']

class WorkflowSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Workflow
        fields = '__all__'
        expandable_fields = {
            'validator_groups': (GroupSerializer, {'many': True}),
            'pipeline': PipelineMinimalSerializer
        }
    
class UploadValidationForListSerializer(FlexFieldsModelSerializer):

    same_upload_validations = serializers.SerializerMethodField()
    def get_same_upload_validations(self, obj):
        validations = UploadValidation.objects.filter(upload=obj.upload.id).exclude(id=obj.id)
        serializer = OtherUploadValidationForListSerializer(validations, many=True)
        return serializer.data
    
    class Meta:
        model = UploadValidation
        fields = '__all__'
        expandable_fields = {
            'upload': UploadSerializer,
            'group': GroupSerializer,
            'workflow': WorkflowSerializer
        }

class OtherUploadValidationForListSerializer(FlexFieldsModelSerializer):
    
    class Meta:
        model = UploadValidation
        fields = '__all__'