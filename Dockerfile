FROM ubuntu:focal

COPY . /app

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-urllib3 python3-pip sshpass mysql-client postgresql-client git rsync

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "/app/main.py"]
