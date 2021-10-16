#FROM python:3.6-alpine

#RUN pip install virtualenv
#RUN apt-get install python-virtualenv
#RUN virtualenv -p /usr/bin/python3.6 /losd-env
#RUN . /losd-env/bin/activate

FROM ubuntu:16.04

USER root

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv
RUN python3.6 -m pip install pip --upgrade
RUN python3.6 -m venv /losd-env
RUN . /losd-env/bin/activate

COPY ./LOSD-RDFconverterAPI /LOSD-RDFconverterAPI
WORKDIR /LOSD-RDFconverterAPI
RUN pip install -r requirements.txt
COPY ./LOSD-RDFconverterAPI/supervisor_app.conf /etc/supervisor_app.conf
EXPOSE 5000
CMD ["uwsgi", "/LOSD-RDFconverterAPI/losd_api.ini"]

