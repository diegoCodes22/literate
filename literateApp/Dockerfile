FROM python:3.9-bullseye

WORKDIR /src

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src src/

#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
CMD ["python3", "app.py"]
