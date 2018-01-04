# simple docker image doing nothing
FROM alpine:latest

RUN apk add --no-cache \
    bash

ADD test.sh /

CMD ["/bin/sh", "/test.sh"]
