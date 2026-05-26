#!/usr/bin/env bash
set -o errexit

cd frontend
npm ci
npm run build
cd ..

cd backend
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_demo
