FROM python:3.10-slim

WORKDIR /usr/src/app

# Healtcheck
RUN apt-get update -y
RUN apt-get install -y curl
HEALTHCHECK --interval=1m --timeout=10s --start-period=1m --retries=3 \
    CMD curl -f http://127.0.0.1:8000/healthcheck || exit 1

EXPOSE 8000

RUN apt-get install -y gettext

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python3 manage.py collectstatic --noinput
RUN django-admin compilemessages --ignore venv

ENTRYPOINT ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
