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

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAdminUser 
from rest_framework.response import Response

from django.utils import translation, timezone, dateformat
from django.utils.translation import gettext as _
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.template import loader
from django.conf import settings

from . models import FileUpload, AllowedFileType, Config, Upload, MetadataValue, UploadValidation, ValidatorGroup
from . apps import FileRepoConfig as FC
from . forms import UploadFileForm
from rest_framework import status

from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError

import pyexcel
import csv
import os
import logging

logger = logging.getLogger(__name__)



@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAdminUser ])
def export_users(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="eUploader_users.csv"'
    
    users = User.objects.all()
    writer = csv.writer(response)
    writer.writerow(['Email', 'Token'])
    for user in users:
        try:
            token = Token.objects.get(user=user)
        except:
            token = ""
        if user.email:
            writer.writerow([user.email, str(token)])
    return response

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAdminUser ])
def import_users(request):
    excel_dir = f'{os.getcwd()}/file_repo/import/users/'
    files = os.listdir(excel_dir)

    for f in files:
        data = pyexcel.iget_records(file_name=f'{excel_dir}{f}')
        for row in data:
            user_data = {k.upper():v for k,v in row.items()}
            if 'EMAIL' not in user_data:
                continue
            
            if not user_data["EMAIL"]:
                continue
            
            email = user_data["EMAIL"]

            try:
                user = User.objects.create_user(username=email, email=email)
            except IntegrityError:
                user = User.objects.get(username=email)

            if 'TOKEN' not in user_data or not user_data["TOKEN"]:
                try:
                    Token.objects.create(user=user)
                except IntegrityError:
                    continue
            else:
                try:
                    Token.objects.create(user=user, key=user_data["TOKEN"])
                except IntegrityError:
                    Token.objects.filter(user=user).update(key=user_data["TOKEN"])
    return Response("Users imported")
