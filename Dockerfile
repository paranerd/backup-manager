FROM ubuntu:focal

COPY . /app

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-urllib3 python3-pip sshpass mysql-client postgresql-client git

RUN pip3 install -r requirements.txt

RUN /bin/echo -e '#!/bin/bash\npython3 /app/main.py --backup "$@"' > /usr/bin/backup && \
    chmod +x /usr/bin/backup

RUN /bin/echo -e '#!/bin/bash\npython3 /app/main.py --add' > /usr/bin/add && \
    chmod +x /usr/bin/add
