FROM python:3.10-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python3 manage.py collectstatic --noinput

ENTRYPOINT ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
