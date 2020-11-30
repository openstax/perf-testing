# Performance Testing - response-validator
This repository contains configurations and scripts needed to automate the
performance and scaling behavior for OpenStax `event-capture-api`.  

## Quick Start (Interactive testing)

Deploy Event Capture API to a sandbox environment.  Be sure the sandbox's 
name has "loadtesting" in the env name (this bypasses normal accounts
user authentication)

The [locustfile.py](locustfile.py) in this directory has tasks to create 
events.

An example locust command to run would be:
```
locust -H https://event-capture-dec11-loadtesting.sandbox.openstax.org
```
Then access `https://localhost:8089` to run the load tests
