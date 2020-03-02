#!/bin/bash
cd /src/payment_system
sh /scripts/prepare_services.sh
rm db.sqlite3
python3 manage.py migrate
python3 manage.py test