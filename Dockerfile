FROM python:3.9-slim

LABEL maintainer="Robin Rottier"
LABEL repos="https://github.com/robinrottier/pihome-gateway-hack"
LABEL org.opencontainers.image.source="https://github.com/robinrottier/pihome-gateway-hack"

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pihome-gateway-hack.py ./

CMD [ "python", "./pihome-gateway-hack.py" ]
