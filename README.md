This repository contains configurations and scripts needed to automate the
performance and scaling behavior ("load testing") for openstax services.  The
code uses the `locust` load-generation framework (https://locust.io) and
`bokeh` (https://bokeh.pydata.org/en/latest/) for realtime visualization of
loads.




## Why `Locust`?

`Locust` is a "load tests as code" framework. Historically, most major
load-test frameworks either use complex GUIs or structured configuration files
(XML or YAML) to define the tests and their relationships. `Locust` leverages
the same sort of syntax used by pytest and pyunit uses for unit tests to define
load tests. Structurally, that means the developer writes small load functions
in python, and define these as tasks of an HTTPLocust-derived class.

This class or classes are then used at run-time by the load-testing framework
to scale tests against a run-time defined target, using a run-time defined set
of load generators. This means tests can be built and used "in the small" with
local servers and test generators, then redeployed without code changes against
multi-server deployments, using a collection of multi-server load generators,
aggregating the resulting data, autmatically.

Practically, what this means is that the developer writes a dedicated
simplified client in python that exercises the server-APIs in the same pattern
as the usual browser-based javascript client. The developer uses their
knowledge of the APIs, or extracts the required information from webdev tools,
such as Chrome Dev tools, or, more generally, via a man-in-the-middle proxy, to
record what URLs are called with what parameters, to write the individual test
scenarios.

Since the tests are code, complexity can be handled exactly like it would be in
any other client: factoring out common components (such as the token extraction
and header settings needed to pass Rails CSRF security checks) so as to keep
the flow of the tests clear, and easy to reason about.


## Why `Bokeh`?

