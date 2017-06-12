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

That will generate run_summary.TIMESTAMP.json and full_itins.TIMESTAMP.json
That one can do with what one pleases.

To generate a report run

    $ python report.py filename1.json filename2.json

Where a file name corresponds to a run_summary file created earlier

To generate an HTML report, run

    $ python hreport.py f1 [fn2 [fn3 ...]] > report.html

## Routing performance and regression detection

Generate a benchmark file:

    $ python otpprofiler.py hostname

When data or OTP changes, generate a test file:

    $ python otpprofiler.py hostname

Then run comparison:

    $ python compare.py benchmark_profile.json new_profile.json
