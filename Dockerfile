FROM node:6
MAINTAINER Digitransit version: 0.1

RUN mkdir -p /opt/OTPQA

WORKDIR /opt/OTPQA

ENV TARGET_HOST https://dev-api.digitransit.fi
ENV TARGET_ROUTER finland
ENV OTPQA_COUNT 200

ADD . /opt/OTPQA

RUN apt-get update && \
  apt-get install -y python-scipy python-sklearn python-pip python-numpy curl

RUN pip install future
RUN pip install grequests
RUN pip install unicodecsv
RUN pip install utm

EXPOSE 8000

CMD python otpprofiler_json.py ${TARGET_HOST} ${TARGET_ROUTER} && \
  python -m SimpleHTTPServer

