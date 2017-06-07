FROM node:6
MAINTAINER Digitransit version: 0.1

RUN mkdir -p /opt/OTPQA

WORKDIR /opt/OTPQA

ENV TARGET_HOST dev-api.digitransit.fi

ADD . /opt/OTPQA

RUN apt-get update && \
  apt-get install -y python-simplejson python-scipy python-pip curl

RUN pip install grequests

RUN cd data && \
  echo "name,lat,lon" > ../endpoints_custom_hsl.csv && \
  npm install node-fetch && \
  node parse_places.js | tee -a ../endpoints_custom_hsl.csv

RUN python gen_requests.py

EXPOSE 8000

CMD python otpprofiler.py ${TARGET_HOST} && \
  python hreport.py run_summary.*json > report.html && \
  python -m SimpleHTTPServer
