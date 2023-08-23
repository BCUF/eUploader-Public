# eUploader-Public

## Install
### For dev on Windows (Some depedencies may change on other OS)
* Need python >= 3.9.13
```bash
git clone https://github.com/BCUF/eUploader-Public.git
cd eUploader-Public
virtualenv env
env\Scripts\activate
pip install -r require.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Using the demo db
* Need python >= 3.9.13
* Replace db.sqlite3 demo_db.sqlite3
```bash
git clone https://github.com/BCUF/eUploader-Public.git
cd eUploader-Public
virtualenv env
env\Scripts\activate
pip install -r require.txt
python manage.py runserver
```

### admin page http://localhost:8000/admin/
* user: admin
* pwd: adminadmin

### angular frontend url
When using the angular frontend use:
* Uploader page: http://localhost:4200/upload?token=61988a4708afcb4650a6b12eecbcc61c84fe36cd
* Validator page: http://localhost:4200/validation

## Deployment
### Docker 
Coming soon...

## Import/Export
### Import
GET /file_repo/v1/users/import/ will import all users in "eUploader/file_repo/import/users/"

### Export
GET /file_repo/v1/users/export/ will export a .csv file with user that have an email set in Django
