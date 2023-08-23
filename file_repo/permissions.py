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

from rest_framework import permissions

class IsValidator(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Validator'):
            return True
        return False
    
class CanAutomate(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Automation'):
            return True
        return False
    
def is_upload_validator_or_uploader(user, upload):
    # check if the user is the uploader
    if str(upload.user) == str(user.username):
        return True
    # check if the the user is pipeline validator
    for validation in upload.validations.all():
        if validation.group.id in [x.id for x in user.groups.all()]:
            return True
    # check if the user is part of Automation group    
    if user and user.groups.filter(name='Automation'):
        return True   

    return False