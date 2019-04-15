FROM python:2.7

RUN virtualenv -p /usr/bin/python2.7 /losd-env
RUN . /losd-env/bin/activate
COPY ./LOSD-RDFconverterAPI /LOSD-RDFconverterAPI
WORKDIR /LOSD-RDFconverterAPI
RUN pip install -r requirements.txt
EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["losd_api.py"]

