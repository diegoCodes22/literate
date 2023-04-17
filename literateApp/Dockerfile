FROM python:3.9.16-bullseye

WORKDIR /literateApp

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /opt

EXPOSE 8080

CMD ["python", "/opt/app.py", "-m", "flask", "run"]