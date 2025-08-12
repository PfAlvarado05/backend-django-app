web: gunicorn core.wsgi --bind 0.0.0.0:$PORT
web: python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT
