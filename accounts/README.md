# Performance Testing - accounts
This folder contains configurations and scripts needed to automate the
performance and scaling behavior ("load testing") for OpenStax
`accounts`. It also contains a script for generating test users (directions for use below). 

## Quick Start

Do the setup from [the framework README ](../README.md)

The [locustfile.py](locustfile.py) in this directory uses a csv file of users generated using `generate_users.py`.  
Each test user (locust) from the CSV file will cycle through the accounts APIs in the locustfile.

Simplest test case would be:

```
locust -H https://accounts-dev.openstax.org
```
Then access `https://localhost:8089` to run tests

#### Generating test users for use with accounts load tests
You can generate a set of users to use for testing load on accounts.openstax.org using the `accounts/generate_users.py` file.
In `generate_users.py` there are a set of variables in the top that will be required.

- `client_id` and `client_secret` - Retrieve this from the "Load Testing" app that is setup on accounts-dev. You'll have to create a new app if you want to use another environment.
- `create_url` - Usually you want this pointing at https://accounts-dev.openstax.org or http://localhost:2999
- `number_of_accounts_to_create` - the number of users to create. *Note: This will add users to the csv if they already exists, so they might not be new users.*
- `password_for_users` - the password to set for the users you create, all users will have the same password. *Note: If the user already exists, the password will not be changed*

After setting the required variables, you can run this with `python accounts/generate_users.py`, which will create a users.csv file, which is already configured to work with the accounts Locust tests. Assuming you want to load test against accounts-dev, that can be started by running `locust -f accounts/locustfile.py --host=https://accounts-dev.openstax.org` from the top level of perf-testing.
