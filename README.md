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
python manage.py makemigrations file_repo
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Important
### Groups in admin
* add a group named "Validator" for the validator users
* add a group named "Automation" for the automation users
* these group names above are strictly reserved for their usage

## Using the demo db
* After the installation, replace db.sqlite3 with demo_db.sqlite3 in the settings.py line 154
* Install the [frontend](https://github.com/BCUF/eUploader-Frontend-Public) and run it (using "ng serve")

### django admin page 
http://localhost:8000/admin/
* user: admin
* pwd: adminadmin

### File Upload page
http://localhost:4200/upload?token=80886113eac6d13e33e3d1d844e8878aa796f904

### Validation page
http://localhost:4200/validation
* validation user 1: ValidationUserX
* validation pwd 1: ValidationUserXValidationUserX
* validation user 2: ValidationUserY
* validation pwd 2: ValidationUserYValidationUserY

## Tools
### User import
GET /file_repo/v1/users/import/ will import all users in "eUploader/file_repo/import/users/"

### User export
GET /file_repo/v1/users/export/ will export a .csv file with user that have an email set in Django
