FROM python:3.11

WORKDIR /usr/src/app

RUN pip --default-timeout=300 install open-webui

CMD ["open-webui", "serve"]