# Performance Testing - response-validator
This repository contains configurations and scripts needed to automate the
performance and scaling behavior ("load testing") for OpenStax
`response-validator`.  This is a simple service, using Flask to provide only a
single (useful) endpoint: `/validate` (there is also `/ping` for testing)

## Quick Start (Interactive testing)

Do the setup from [the framework README ](../README.md)

This should give you functional (and running) `bokeh` plot server.

Since the validator server is simple, use any of the means described in
the README.md at the top of its repository (https://github.com/openstax/response-validator/)
to create a running instance to test.

The [locustfile.py](locustfile.py) in this directory uses a text file of [100 test urls](urls.txt),
taken from actual student responses.  Each test user (locust) will access all 100 urls, in random order. 

Simplest test case would be:

```
locust -H https://validator-dev.openstax.org
```
Then access `https://localhost:8089` to run tests
