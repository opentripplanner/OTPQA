OTPQA
=====

## Docker quickstart

1. Build image: `docker build -t hsldevcom/otpqa .`
2. Run tests against host `docker run -p8000:8000 -e TARGET_HOST=dev-api.digitransit.fi hsldevcom/otpqa`
3. Check results: http://localhost:8000/report.html


## Original OTPQA docs

Keep track of changes in OTP performance as development progresses, and catch breaking changes to input data sets by observing changes in routing results.

You will need Python (2.x) and some Python libraries. For the libraries, on a Debian based system like Ubuntu you can run:

`$ sudo apt-get install python-simplejson python-scipy`

We also use grequests to handle multiple concurrent HTTP requests.

`$ sudo pip install grequests`

Generate random points with:

    $ python gen_points.py dirname num_points

`dirname` is the name of a directory with OSM and GTFS data.

Generate the request parameters and save the request endpoints with:

    $ python gen_requests.py

It takes no arguments, assumes the presence of endpoints_random.csv and endpoints_custom.csv in the same directory.

Then run the profiler with

    $ python otpprofiler.py hostname

Here hostname can be briefly a digitransit service API root address such as 'api.digitransit.fi',
or a full path to a local OTP instance routing: 'localhost:9080/otp/routers/default'.

That will generate run_summary.TIMESTAMP.json and full_itins.TIMESTAMP.json
That one can do with what one pleases.

To generate a report run

    $ python report.py filename1.json filename2.json

Where a file name corresponds to a run_summary file created earlier

To generate an HTML report, run

    $ python hreport.py f1 [fn2 [fn3 ...]] > report.html


## Routing performance and regression detection

In order to run to run the otpprofiler.py, you need to have requests.json in the same directory.
You can generate it by running `PIWIK_TOKEN=<some_valid_API_token> python` generate_piwik_requests.py and then 
`python gen_requests.py`.

Generate a benchmark file:

    $ python otpprofiler.py -o hostname

    where hostname is, for example, http://localhost:8888/otp/routers/hsl/
    When using the flag -o, profiler generates run_summary and full_itins JSON files.
    run_summary file can then be later used as a comparison file.
    You can also use parameters when running the profiler such as -i 5 and then five itineraries are fetched instead of just one.
    You can force profiler to use certain modes in requests with -m 'MODE1,MODE2,MODE3' where these MODE values should be valid OTP traverse modes.

When data or OTP changes, generate a test file:

    $ python otpprofiler.py -o hostname

Then run comparison:

    $ python compare.py benchmark_profile.json new_profile.json

The test uses, by default, a time threshold of 60 seconds. This means that changes less than one minute in route duration are not considered
significant in regression detection. A custom threshold can be set using -t parameter: python compare.py -t 10 ...

The test computes a performance measurement ratio 100% * (#equally good routes / #all routes). If the ratio is below the given limit value
(parameter -l , default=95), the test exits with code 1. So, by default, test fails if 5% of routes have become significantly slower.

By default, otpprofiler.py tries to fetch only one itinerary per request. It is possible to control the number of requested itineraries with parameter -i (default 1). When using parameter -i in compare.py, additional comparison of number of itineraries returned by OTP is done. Parameter -m adds a comparison of number of different modes (WALK, BICYCLE and CAR are only counted towards this number if they are the only mode(s) in some request) used in the different itineraries in each route. By default, the threshold for both additional comparisons is 1 but you can control the thresholds with -it (for itineraries) and -mt (for modes). You can also compare
number of legs in the first itinerary by using -legs (and -legt to change the threshold, default is 1). If you want to know how some changes affect walking or cycling
speeds, use -s (-st allows you to change the threshold, default 0.2 (m/s)). To evaluate if queries are faster/slower to execute, use -p (with -tt you can give threshold
value for totaltime difference in ms and with -at average time threshold value in ms).
