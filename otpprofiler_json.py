import pprint

import sys

import os

import otpprofiler
import json
import hreport


RATIO_LIMIT = 0.2

f = open('otpqa_router_requests.json')
router_sites = json.load(f)
f.close()

OTP_URL = 'https://dev-api.digitransit.fi/routing/v1/routers/%s'
if len(sys.argv) >= 2:
    OTP_URL = sys.argv[1]

test_routers = set(router_sites.keys())
if len(sys.argv) >= 3:
    test_routers = set(sys.argv[2].split(','))

skipped_sites = set()
if len(sys.argv) >= 4:
    skipped_sites = set(sys.argv[3].split(','))

print('TARGET OTP',OTP_URL)

for router in test_routers:
  if router in router_sites:
    rsites = router_sites[router]
    print(router)

    router_url = OTP_URL
    if OTP_URL.find('%s') > -1:
        router_url = OTP_URL % router

    f = open('otpqa_report_%s.html' % router, 'w+')
    for site in rsites:
        if site['name'] in skipped_sites:
            print("Skipping tests for " + site['name'])
            continue
        print(site['name'])
        nfailed = 0
        nnone = 0
        totaln = 0

        params = {
            'date': otpprofiler.DATE,
            'time': '14:00',
            'retry': 5,
            'count': int(os.getenv('OTPQA_COUNT',200)),
            'notes': None,
            'fast': False,
            'profile': False,
            'host': router_url,
            'itineraries': 2,
            'output': False,
            'modes': None

        }
        response_json = otpprofiler.run(params, requests_json=site['requests'])

        for r in response_json['responses']:
            if not 'itins' in r:
                nfailed += 1
                continue

            if all((itin['walk_limit_exceeded'] for itin in r['itins'])):
                nfailed += 1
                continue

            if len(r['itins']) == 0:
                nnone += 1

        totaln += float(len(response_json['responses']))

        ratio = (nfailed + nnone) / totaln

        print('total:', totaln, 'failed:', nfailed, 'none:', nnone, 'ratio:', ratio)

        report_html = ''.join(hreport.main(None, response_json, site['name']))

        f.write('<h1>%s</h1>' % site['name'])
        f.write(report_html)

        if ratio > RATIO_LIMIT:
            print('FAILED RATIO >',RATIO_LIMIT)
            f.close()
            sys.exit(1)

    f.close()

sys.exit(0)

