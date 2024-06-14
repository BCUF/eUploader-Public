FROM python:3.9.18-alpine3.18

LABEL maintainer="bcu_informatique[at]fr.ch"
LABEL description="eUploader"

# Copy in your requirements file
ADD require_linux.txt /eUploader/require_linux.txt
ADD deployment/supervisord.conf /etc/supervisord.conf
ADD deployment/nginx/eUploader.conf-nginx /etc/nginx/conf.d/eUploader.conf
ADD deployment/nginx/nginx.conf /etc/nginx/nginx.conf
WORKDIR /eUploader/

# Django
RUN set -ex \
    && apk add libmagic \
    && apk add --no-cache --virtual .build-deps \
            gcc \
            make \
            libc-dev \
            musl-dev \
            linux-headers \
            pcre-dev \
            libxml2-dev \
            libxslt-dev \
            nginx \
            py3-libxml2 \
            python3-dev \
            py3-virtualenv \
    && /usr/bin/virtualenv /eUploader/venv \
    && /eUploader/venv/bin/pip install -U pip \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "/eUploader/venv/bin/pip install --no-cache-dir -r //eUploader/require_linux.txt" \
    && runDeps="$( \
            scanelf --needed --nobanner --recursive /eUploader/venv \
                    | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                    | sort -u \
                    | xargs -r apk info --installed \
                    | sort -u \
    )" \
    && apk add --virtual .python-rundeps $runDeps \
    && apk del .build-deps \
    && apk add gettext

# SFTP
# RUN echo "@community http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
#     apk add --no-cache bash shadow@community openssh openssh-sftp-server && \
#     sed -i 's/GROUP=1000/GROUP=100/' /etc/default/useradd && \
#     mkdir -p /var/run/sshd && \
#     rm -f /etc/ssh/ssh_host_*key*
# COPY deployment/sftp/sshd_config /etc/ssh/sshd_config
# COPY deployment/sftp/create-sftp-user /usr/local/bin/
# COPY deployment/sftp/entrypoint /
# COPY deployment/sftp/users.conf /etc/sftp/users.conf
# RUN chmod +x /usr/local/bin/create-sftp-user && \
#     chmod +x /entrypoint

# Clamd
RUN apk add --no-cache bash clamav clamav-daemon rsyslog wget clamav-libunrar su-exec
COPY deployment/clamav/conf /etc/clamav
COPY deployment/clamav/bootstrap.sh /
COPY deployment/clamav/check.sh /
RUN dos2unix /bootstrap.sh
RUN dos2unix /check.sh
RUN dos2unix /etc/clamav/clamd.conf
RUN dos2unix /etc/clamav/freshclam.conf
RUN mkdir -p /var/run/clamav
RUN chown clamav:clamav /var/run/clamav
RUN chmod 750 /var/run/clamav \
    && chown -R clamav:clamav /bootstrap.sh /check.sh /etc/clamav \
    && chmod u+x /bootstrap.sh /check.sh 

# Nginx
RUN apk add --no-cache supervisor nginx
WORKDIR /eUploader/src/
ADD . /eUploader/src/

# nginx & SFTP & Clamd will listen on this port
# EXPOSE 22 80 3310/tcp
EXPOSE 80 3310/tcp

# delete default nginx config
# RUN rm /etc/nginx/conf.d/default.conf

#prepare user and group
RUN adduser -D -u 1000 uwsgi
RUN addgroup nginx uwsgi

# Add any custom, static environment variables needed by Django or your settings file here:
#ENV DJANGO_SETTINGS_MODULE=my_project.settings.deploy
RUN mkdir -p /storage \
    && chown -R uwsgi /storage \
    && chgrp -R uwsgi /storage

RUN mkdir -p /upload/public/ \
    && chown -R uwsgi /upload \
    && chgrp -R uwsgi /upload \
    && chown -R uwsgi /upload/public \
    && chgrp -R uwsgi /upload/public

RUN mkdir -p /var/tmp/nginx

RUN mkdir -p /eUploader_log \
    && chown -R uwsgi /eUploader_log \
    && chgrp -R uwsgi /eUploader_log \
    && touch /eUploader_log/info.log \
    && chown -R uwsgi /eUploader_log/info.log \
    && chgrp -R uwsgi /eUploader_log/info.log

RUN mkdir /var/log/supervisord/

# uWSGI configuration (customize as needed):
ENV UWSGI_VIRTUALENV=/eUploader/venv UWSGI_WSGI_FILE=eUploader/wsgi.py UWSGI_MASTER=1 UWSGI_WORKERS=2 UWSGI_THREADS=8 UWSGI_UID=1000 UWSGI_GID=1000 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy

# Call collectstatic (customize the following line with the minimal environment variables needed for manage.py to run):
RUN /eUploader/venv/bin/python3 manage.py collectstatic --noinput
RUN cp -r /eUploader/src/file_repo/static/file_repo/assets/ /eUploader/src/static/assets
RUN /eUploader/venv/bin/python3 manage.py makemigrations
RUN /eUploader/venv/bin/python3 manage.py makemigrations file_repo
RUN /eUploader/venv/bin/python3 manage.py migrate
RUN chown -R uwsgi /eUploader
RUN chgrp -R uwsgi /eUploader

#SFTP Folder
# RUN mkdir -p /eUploader/src/upload/public && \
#     chown root:root /eUploader/src/upload/ && \
#     chmod 755 /eUploader/src/upload/ && \
#     chmod 777 /eUploader/src/upload/ && \
#     ln -s /eUploader/src/upload /upload && \
#     chown root:root /upload && \
#     chmod 755 /upload


# Start supervisor
CMD ["/usr/bin/supervisord"]
