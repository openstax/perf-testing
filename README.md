# Performance Testing
This repository contains configurations and scripts needed to automate the
performance and scaling behavior ("load testing") for OpenStax services.  The
code uses the `locust` load-generation framework (https://locust.io) and
`bokeh` (https://bokeh.pydata.org/en/latest/) for real-time visualization of
loads.

## Quick Start (Interactive testing)

Create a python3 virtual env (with wheel support)
```
python3 -m venv
source bin/activate
pip install wheel
```
Install locust and bokeh
```
pip install locust bokeh
```

Each OpenStax server has a same-named folder (i.e. `response-validator`)
Check that folder for README.md and files for instructions necessary to
deploy systems to be tested, in appropriate configurations.

Launch the `bokeh` graphing service:
```
bokeh serve --show plotter.py --log-file plotter.log &
```

This should open a new tab in your default browser, loading http://localhost:5006/plotter

Launch the interactive `locust` control server:
```
locust -f <server-under-test>/locustfile.py -H <full-schema-and-host-url>
```
e.g.
```
locust -f response-validator/locustfile.py -H https://validator-qa.openstax.org
```

Then open a browser tab at: http://localhost:8089

Enter target number of users, and how many users to add per minute, and hit "run"

Monitor the progress of the test on both the Locust and Bokeh tabs.



## Why `Locust`?

`Locust` is a "load tests as code" framework. Historically, most major
load-test frameworks either use complex GUIs or structured configuration files
(XML or YAML) to define the tests and their relationships. `Locust` leverages
the same sort of syntax used by pytest and pyunit uses for unit tests to define
load tests. Structurally, that means the developer writes small load functions
in python, and define these as tasks of an HttpLocust-derived class.

This class or classes are then used at run-time by the load-testing framework
to scale tests against a run-time defined target, using a run-time defined set
of load generators. This means tests can be built and used "in the small" with
local servers and test generators, then redeployed without code changes against
multi-server deployments, using a collection of multi-server load generators,
aggregating the resulting data, automatically.

Practically, what this means is that the developer writes a dedicated
simplified client in python that exercises the server-APIs in the same pattern
as the usual browser-based javascript client. The developer uses their
knowledge of the APIs, or extracts the required information from webdev tools,
such as Chrome Developer tools, or, more generally, via a man-in-the-middle
proxy, to record what URLs are called with what parameters, to write the
individual test scenarios.

Since the tests are code, complexity can be handled exactly like it would be in
any other client: factoring out common components (such as the token extraction
and header settings needed to pass Rails CSRF security checks) so as to keep
the flow of the tests clear, and easy to reason about.


## Why `Bokeh`?

Bokeh is a python graphing library that is particularly useful for live
graphing. To be honest, I found an existing example for generating graphs from
`Locust`, and modified it slightly. The live data feed (at
http://localhost:8089/stats/requests ) is a fairly straightforward to parse JSON
feed, updated every 2 seconds by default). In addition, a csv bundle of the data
are available at http://localhost:8089/stats/requests/csv so use of other data
processing tools is straight forward. Lastly, by running `Locust` in a batch mode,
rather than interactively, data and log files are produced in a more usual fashion.
The interactive setup described above is primarily of use for developers working to 
define and improve the performance of the system under test.
