FROM ubuntu:latest
LABEL authors="joseph"

ENTRYPOINT ["top", "-b"]