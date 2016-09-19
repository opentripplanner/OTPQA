FROM node:6
MAINTAINER Digitransit version: 0.1

RUN mkdir -p /opt/OTPQA

WORKDIR /opt/OTPQA

ENV TARGET_HOST dev-api.digitransit.fi

ADD . /opt/OTPQA

RUN apt-get update && \
  apt-get install -y python-simplejson python-scipy curl

RUN curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | python

RUN pip install grequests

RUN cd data && \
  npm install node-fetch && \
  node parse_places.js | tee ../endpoints_custom_hsl

RUN python gen_requests.py 

EXPOSE 8000

CMD python otpprofiler.py ${TARGET_HOST} && \
  python hreport.py run_summary.*json > report.html && \
  python -m SimpleHTTPServer
