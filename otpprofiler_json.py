import pprint

import sys

import os

import otpprofiler
import json
import hreport


RATIO_LIMIT = 0.1

f = open('otpqa_router_requests.json')
router_sites = json.load(f)
f.close()

target_host = 'https://api.digitransit.fi'
if len(sys.argv) >= 2:
    target_host = sys.argv[1]
else:
    print('Usage: python ottprofiler_json.py <target_host> <target_routers>')
    sys.exit(2)

test_routers = set(router_sites.keys())
if len(sys.argv) == 3:
    test_routers = set(sys.argv[2].split(','))

OTP_URL_TEMPLATE = '%s/routing/v1/routers/%%s' % target_host
print('OTP TEMPLATE',OTP_URL_TEMPLATE)
for router, rsites in ((tr, router_sites[tr]) for tr in test_routers):
    print(router)
    nfailed = 0
    nnone = 0
    totaln = 0
    f = open('otpqa_report_%s.html' % router, 'w+')
    for site in rsites:
        print(site['name'])
        OTP_URL = OTP_URL_TEMPLATE % router

        params = {
            'date': otpprofiler.DATE,
            'time': '14:00',
            'retry': 5,
            'count': int(os.getenv('OTPQA_COUNT',200)),
            'notes': None,
            'fast': False,
            'profile': False,
            'host': OTP_URL

        }
        response_json = otpprofiler.run(params, requests_json=site['requests'])


        for r in response_json['responses']:
            if not 'itins' in r:
                nfailed += 1
                continue
            if len(r['itins']) == 0:
                nnone += 1

        totaln += float(len(response_json['responses']))


        report_html = ''.join(hreport.main(None, response_json, site['name']))

        f.write('<h1>%s</h1>' % site['name'])
        f.write(report_html)
    f.close()

    ratio = (nfailed + nnone) / totaln

    print('total:', totaln, 'failed:', nfailed, 'none:', nnone, 'ratio:', ratio)

    if ratio > RATIO_LIMIT:
        print('FAILED RATIO >',RATIO_LIMIT)
        sys.exit(1)


    sys.exit(0)

