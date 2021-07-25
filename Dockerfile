FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
