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

from rest_framework import viewsets, mixins
from django.contrib.auth.models import User, Group
from .models import Pipeline, Upload, FileUpload, MetadataValue, Note, UploadValidation, MetadataFormsField, Workflow
from rest_framework import status
from rest_framework.response import Response
from .serializers import PipelineSerializer, UserSerializer, UserMinimalSerializer, UploadSerializer, PipelineMinimalSerializer, NoteSerializer, UploadMinimalSerializer, FileUploadSerializer, MetadataValueSerializer, PipelineFormsFieldsNoScopeSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
import json, os
from .flex_serializers import UploadValidationForListSerializer, UploadValidationSerializer
from rest_framework import mixins
from .permissions import IsValidator, CanAutomate, is_upload_validator_or_uploader, IsUploaderOrValidatorForFileUpload, IsUploaderOrValidatorForUpload, IsUploaderOrValidatorForFileUpload
from rest_framework import filters
from django.http import FileResponse
from datetime import datetime

@api_view(['GET'])
def download_file(request, id):
    try:
        file = FileUpload.objects.get(id=id)
        if is_upload_validator_or_uploader(request.user, file.upload):
            filename = os.path.basename(file.uploaded_file.path)
            path = file.uploaded_file.path
            response = FileResponse(open(path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    except FileUpload.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


class PipelineViewSet(viewsets.ReadOnlyModelViewSet):

    def list(self, request):
        if(hasattr(request.user, 'custom')):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        else:
            pipeline = Pipeline.objects.all().order_by('id')
            serializer = PipelineSerializer(pipeline, many=True)
            return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        An uploader can see only its own pipeline
        """
        pipeline = Pipeline.objects.get(id=pk)
        if(hasattr(request.user, 'custom')):
            if pipeline:
                if pipeline != request.user.custom.pipeline:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
                else:
                    """
                    if the user is an uploader then he must get only no scope fields
                    """
                    serializer = PipelineFormsFieldsNoScopeSerializer(pipeline)
                    return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            if not pipeline:
                return Response(status=status.HTTP_404_NOT_FOUND)
            serializer = PipelineSerializer(pipeline)
            return Response(serializer.data)
        
class PipelineMinimalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pipeline.objects.all().order_by('id')
    serializer_class = PipelineMinimalSerializer

class NoteViewSet(viewsets.ModelViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    permission_classes = [IsValidator]
    queryset = Note.objects.all().order_by('-created')
    serializer_class = NoteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['upload']
    pagination_class = None

class UploadViewSet(viewsets.ModelViewSet):
    serializer_class = UploadSerializer
    permission_classes = [IsUploaderOrValidatorForUpload]

    def get_queryset(self):
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = Upload.objects.filter(uploaded_at__gte=date_from).order_by('id')
        else:
            queryset = Upload.objects.all()
        return queryset
    
    def create(self, request):
        # if the last upload has the state INIT we don't create a new one.
        upload = Upload.objects.filter(user=request.user).last()
        if upload:
            if upload.status == Upload.Status.INIT or upload.status == Upload.Status.FILE_UPLOADED:
                upload.uploaded_at = datetime.now()
                upload.save()
                serializer = UploadSerializer(upload)
                return Response(serializer.data)
        serializer = UploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=self.request.user, 
                pipeline=self.request.user.custom.pipeline, 
                same_meta_for_each_file=self.request.user.custom.pipeline.default_same_metadata_for_each_file)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

"""
Return only the validated uploads by pipeline
"""
@api_view(['GET'])
@permission_classes([CanAutomate])
def validated_upload(request, pipeline_id):

    try:
        pipeline = Pipeline.objects.get(id=pipeline_id)
    except Pipeline.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    upload_ids = set()

    for workflow in Workflow.objects.filter(pipeline=pipeline):
        for validation in workflow.upload_validations.all():
            if all(v.state == UploadValidation.State.VALIDATED_OK for v in UploadValidation.objects.filter(upload__id=validation.upload.id)):
                upload_ids.add(validation.upload.id)

    uploads = Upload.objects.filter(id__in=upload_ids)

    paginator = PageNumberPagination()
    paginator.page_size = api_settings.PAGE_SIZE
    result_page = paginator.paginate_queryset(uploads, request)
    serializer = UploadSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


class UploadsByPipeline(APIView):

    def get(self, request, pipeline_id):

        pipeline = None
        try:
            pipeline = Pipeline.objects.get(id=pipeline_id)
        except Pipeline.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        date_from = request.query_params.get('date_from')
        upload_status = request.query_params.get('status', "COMPLETED").upper()
        uploads = []
        
        if request.user and request.user.groups.filter(name='Automation'):

            # find the users which linked the requested pipeline
            upload_users = []
            for upload in Upload.objects.all():
                if hasattr(upload.user, 'custom') and (str(upload.user.custom.pipeline.id) == str(pipeline_id)):
                    upload_users.append(upload.user)

            if date_from:
                uploads = Upload.objects.filter(user__in=upload_users).filter(status=upload_status).filter(uploaded_at__gte=date_from).order_by('id')
            else:
                uploads = Upload.objects.filter(user__in=upload_users).filter(status=upload_status).order_by('id')
        else:

            if date_from:
                uploads = Upload.objects.filter(user=request.user).filter(user__custom__pipeline=pipeline).filter(status=upload_status).filter(uploaded_at__gte=date_from).order_by('id')
            else:
                uploads = Upload.objects.filter(user=request.user).filter(user__custom__pipeline=pipeline).filter(status=upload_status).order_by('id')

        paginator = PageNumberPagination()
        paginator.page_size = api_settings.PAGE_SIZE
        result_page = paginator.paginate_queryset(uploads, request)
        serializer = UploadSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

class UploadValidationViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    serializer_class = UploadValidationForListSerializer
    permission_classes = [IsValidator]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'

    def get_queryset(self):

        user_groups = self.request.user.groups.all().order_by("id")

        ordering = self.request.GET.get('ordering')

        if ordering:
            if ordering.lower() == "upload__uploaded_at" or ordering.lower() == "-upload__uploaded_at":
                validations = UploadValidation.objects.filter(group__in=user_groups).order_by(ordering)
            elif ordering.lower() == "upload__id" or ordering.lower() == "-upload__id":
                validations = UploadValidation.objects.filter(group__in=user_groups).order_by(ordering)
            else:
                validations = UploadValidation.objects.filter(group__in=user_groups).order_by("id")
        else:
            validations = UploadValidation.objects.filter(group__in=user_groups).order_by("id")

        return validations

class FileUploadViewSet(viewsets.ModelViewSet):
    serializer_class = FileUploadSerializer
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsUploaderOrValidatorForFileUpload]
    filterset_fields = ['upload']

    def get_queryset(self):
        queryset = FileUpload.objects.all().order_by('id')
        return queryset
    
    def create(self, request):
        
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserByToken(APIView):

    def get(self, request, token):
        try:
            user=Token.objects.get(key=token).user
            serializer = UserMinimalSerializer(user)
            return Response(serializer.data)
        except Pipeline.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
def file_metadata(request, file_id):
    
    try:

        file = FileUpload.objects.get(id=file_id)

        try:

            upload = Upload.objects.get(id=file.upload.id)

            if is_upload_validator_or_uploader(request.user, upload):

                data = json.loads(request.body)

                if upload.same_meta_for_each_file:
                    for f in upload.files.all():
                        for d in data:
                            try:
                                
                                m = MetadataValue.objects.get(key=d["key"], file=f)
                                if m.value != d["value"]:
                                    m.value = d["value"]
                                    m.save()
                            except MetadataValue.DoesNotExist:
                                m = MetadataValue()
                                m.file = f
                                m.key = d["key"]
                                m.value = d["value"]
                                m.save()

                else:
                    for d in data:
                        try:
                            m = MetadataValue.objects.get(key=d["key"], file=file)
                            if m.value != d["value"]:
                                m.value = d["value"]
                                m.save()
                        except MetadataValue.DoesNotExist:
                            m = MetadataValue()
                            m.file = file
                            m.key = d["key"]
                            m.value = d["value"]
                            m.save()

                """
                Create a validation if the user is an uploader
                """
                if hasattr(request.user, "custom"):

                    # check if the upload already has a validation
                    has_validation_already = upload.validations.count() > 0

                    if not has_validation_already:

                        groups = set()

                        workflows = request.user.custom.pipeline.workflows.all()

                        if not has_validation_already:

                            for workflow in workflows:
                                validator_groups = Group.objects.filter(workflow=workflow)
                                for group in validator_groups:
                                    groups.add(group)
                                    
                            # Create validations
                            for group in groups:
                                validation = UploadValidation()
                                validation.upload = upload
                                validation.group = group
                                validation.workflow = workflows[0]
                                validation.save()


                serializer = FileUploadSerializer(file)
                return Response(serializer.data)
            
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Upload.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
    except FileUpload.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)