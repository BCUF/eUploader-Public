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

from django.urls import path, re_path, include
from . import views, api_views
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'file_repo'

"""
router allows to get all pipelines for example when using url /api/pipeline/ 
and automatically get 1 pipeline using /api/pipeline/1/ adding pipeline's id
"""
router = routers.DefaultRouter()
router.register(r'pipeline', api_views.PipelineViewSet, basename="pipeline")
router.register(r'pipeline-minimal', api_views.PipelineMinimalViewSet, basename="pipeline-minimal")
router.register(r'upload', api_views.UploadViewSet, basename="upload")
router.register(r'file', api_views.FileUploadViewSet, basename="file")
router.register(r'metadata-value', api_views.MetadataValueViewSet, basename="metadata-value")
router.register(r'note', api_views.NoteViewSet, basename="note")
router.register(r'upload-validation', api_views.UploadValidationViewSet, basename="upload-validation")

urlpatterns = [
    re_path(r'^v1/users/export/$', views.export_users, name='export_users'),
    re_path(r'^v1/users/import/$', views.import_users, name='import_users'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/pipeline-uploads/<int:pipeline_id>/', api_views.UploadsByPipeline.as_view(), name='pipeline-uploads'),
    path('api/user-by-token/<str:token>/',  api_views.UserByToken.as_view(), name='user-by-token'),
    path('api/file/<int:file_id>/metadata/',  api_views.file_metadata, name='file-metadata'),
    path('api/download-file/<int:id>/',  api_views.download_file, name='download-file'),
    path('api/api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/validated-upload/<int:pipeline_id>/', api_views.validated_upload, name='validated-upload'),
]