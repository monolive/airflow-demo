FROM alpine:latest

RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    py-cffi \
    gcc \
    make \
    musl-dev \
    openssl-dev \
    && pip3 install datetime paramiko ConfigParser

VOLUME /var/sftp-data

ADD copy-files.py /config/
ADD id_rsa /config/
ADD known_hosts /config/

CMD ["/usr/bin/python3", "/config/copy-files.py"]
