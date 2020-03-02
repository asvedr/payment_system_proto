#!/bin/bash

sh /scripts/prepare_services.sh
cd /src/payment_system
python3 manage.py migrate
python3 manage.py add_init_data
celery worker -A payment_system worker &
celery beat -A payment_system &
uwsgi --http :8080 --wsgi-file payment_system/wsgi.py
