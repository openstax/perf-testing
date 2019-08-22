import csv
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

## VARIABLES
client_id = ''
client_secret = ''
create_url = 'https://accounts-dev.openstax.org/api/user/find-or-create/'
number_of_accounts_to_create = 2
password_for_users = ""

# OAUTH FLOW
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(token_url='https://accounts-dev.openstax.org/oauth/token', client_id=client_id,
        client_secret=client_secret)

# ACCOUNT CREATION
headers = {"Content-Type": "application/json"}

with open('users.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['type', 'email', 'password'])

    for i in range(1, number_of_accounts_to_create + 1):
        email = "invisible+{}@rice.edu".format(i)
        username = "Testy{}".format(i)
        data = '''{{"email": "{email}",
          "first_name": "{username}",
          "last_name": "McTesty",
          "password": "{password}",
          "is_test": true
        }}'''.format(email=email, username=username, password=password_for_users)

        response = oauth.post(create_url, data=data, headers=headers)

        filewriter.writerow(['test', email, password_for_users])

        print(response.content)