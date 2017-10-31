from __future__ import print_function
from future.standard_library import install_aliases
import json
import numpy as np
import math
from datetime import datetime

install_aliases()
from urllib.parse import urlparse, parse_qs

def parsetime(aa):
    if aa is None:
        return None

    return float(aa.split()[0])


def humanize(lt):
    minf = math.modf(lt/60.0)
    hf = math.modf(minf[1]/60.0)
    os = ''
    if hf[1] > 0:
        os += '%d h ' % (hf[1])
        os += '%d min ' % (hf[0]*60)
    else:
        if minf[1] > 0:
            os += '%d min ' % minf[1]

    os += '%d sec' % (minf[0] * 60)
    return os


def main(filenames, input_blob=None, dt_url=None):
    if (filenames is None or len(filenames) == 0) and input_blob is None:
        return

    if input_blob is None:
        datasets = []
        for fn in filenames:
            blob = json.load(open(fn))
            dataset = dict([(response["id_tuple"], response) for response in blob['responses']])
            datasets.append(dataset)
    else:
        datasets = [dict([(response["id_tuple"], response) for response in input_blob['responses']]), ]

    id_tuples = datasets[0].keys()

    if len(id_tuples) == 0:
        print("Input does not contain any data")
        exit()

    yield "<html>"
    yield """<head><style>table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
th, td {
    text-align: left;
    vertical-align:top;
}</style></head>"""

    yield """<table border="1">"""

    dataset_total_times = dict(zip(range(len(datasets)), [[] for x in range(len(datasets))]))
    dataset_avg_times = dict(zip(range(len(datasets)), [[] for x in range(len(datasets))]))
    dataset_fails = dict(zip(range(len(datasets)), [0] * len(datasets)))

    for id_tuple in id_tuples:
        otpurl = ''
        if dt_url is not None:

            otpurl = datasets[0][id_tuple]['url']
            otpurl_parsed = urlparse(otpurl)
            otpurl_params = parse_qs(otpurl_parsed.query)

            otptst = datetime.strptime('%s %s' % (otpurl_params['date'][0],otpurl_params['time'][0]),'%Y-%m-%d %H:%M')
            otptst = (otptst - datetime(1970, 1, 1)).total_seconds()

            dturl = 'http://' + dt_url + '/reitti/from::%s/to::%s?time=%d' % \
                                          (datasets[0][id_tuple]['from'], datasets[0][id_tuple]['to'],otptst)

        yield """<tr><td rowspan="2" width="120">OTP: <a href="%s">%s</a><br/>DT: <a href="%s">%s</a></td>""" % \
              (otpurl, id_tuple, dturl, id_tuple)
        for i, dataset in enumerate(datasets):
            response = dataset[id_tuple]
            if not 'total_time' in response:
                continue

            dataset_total_times[i].append(parsetime(response['total_time']))
            dataset_avg_times[i].append(parsetime(response['avg_time']))

            yield "<td>%s total, %s avg / %s</td>" % (
                response['total_time'], response['avg_time'], datasets[i][id_tuple]['mode'])
        yield "</tr>"

        for i, dataset in enumerate(datasets):
            yield "<td>"

            response = dataset[id_tuple]

            yield "<table border=1 width=100%><tr>"
            if not 'itins' in response:
                yield "<td style=\"background-color:#EDA1A1\">FAIL</td></tr></table></tr>"
                continue

            if len(response['itins']) == 0:
                dataset_fails[i] += 1
                yield "<td style=\"background-color:#EDA1A1\">NONE</td>"

            for itin in response['itins']:
                filling = list(zip(itin['leg_modes'],(humanize(lt) for lt in itin['leg_times'])))
                if filling == "{}":
                    color = "#EDECA1"
                else:
                    color = "#AEEDA1"
                yield "<td style=\"background-color:%s\"><small>%s</small><br/>walk distance: %.1f km - wait: %s</td>" % (color, filling,itin['walk_distance']/1000.0, humanize(itin['wait_time_sec']))

            yield "</tr></table>"
            yield "</td>"
        yield "</tr>"

    yield "<tr><td>stats</td>"
    for i in range(len(datasets)):
        yield "<td>fails: %s (%.2f%%). total time: median:%.2fs mean:%.2fs</td>" % (
            dataset_fails[i], 100 * dataset_fails[i] / float(len(id_tuples)), np.median(dataset_total_times[i]),
            np.mean(dataset_total_times[i]))
    yield "</tr>"

    yield "</table>"

    yield "</html>"


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("usage: cmd fn1[fn2[fn3...]]")
        exit()

        for line in main(sys.argv[1:]):
            print(line)
