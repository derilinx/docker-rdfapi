FROM python:2.7

RUN virtualenv -p /usr/bin/python2.7 /losd-env
RUN . /losd-env/bin/activate
COPY ./LOSD-RDFconverterAPI /LOSD-RDFconverterAPI
WORKDIR /LOSD-RDFconverterAPI
RUN pip install -r requirements.txt
COPY ./LOSD-RDFconverterAPI/supervisor_app.conf /etc/supervisor_app.conf
EXPOSE 5000
CMD ["uwsgi", "/LOSD-RDFconverterAPI/losd_api.ini"]

