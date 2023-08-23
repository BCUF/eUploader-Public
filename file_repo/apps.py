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

from django.apps import AppConfig

class FileRepoConfig(AppConfig):
    name = 'file_repo'


    # can be overrided as a Config objects in the DB
    # key=FILE_SIZE_LIMIT_IN_BYTE, value=xxx in Byte
    DEFAULT_SIZE_LIMIT_IN_BYTE = 209715200 # 200MB
    LANGUAGE_ACCEPTED = ["fr", "de"]
    VALIDATION_ITEMS_PER_PAGE = 10
