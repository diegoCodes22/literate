FROM python:3.9.16-bullseye

WORKDIR /literateApp

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY literateApp /app
COPY literateDB /app/literateDB

EXPOSE 8080

CMD ["python", "/app/app.py", "-m", "flask", "run"]