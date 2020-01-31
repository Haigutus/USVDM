#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     03.05.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas
import collections
import PublicationFormat

from requests import Session, status_codes, Request
from requests.auth import HTTPBasicAuth

debug = True
source = "send_to_dashboard.xlsx"


data = pandas.read_excel(source, sheet_name=None)

# Create meta dict
meta_dict = collections.OrderedDict()

for _,row in data["meta"].iterrows():

    if str(row.value) == "nan":
        meta_dict[row.key] = None
    else:
        meta_dict[row.key] = row.value

# Create message
message = PublicationFormat.create_message(meta_dict, data["data"], print_message = debug)

# Settings
url      = data["settings"].query("key == 'endpoint'").value.item()
username = data["settings"].query("key == 'username'").value.item()
password = data["settings"].query("key == 'password'").value.item()


# Send data
session = Session()
session.verify = False
session.auth = HTTPBasicAuth(username, password)

post = Request('POST', url, headers={"Content-Type":"application/xml"}, data=message, auth=(username, password))
preapared_post = post.prepare()
response = session.send(preapared_post)


if debug == True:
    print("--- SENT ---")
    print(preapared_post.headers)
    print(preapared_post.body)

    print("\n--- RECIEVED ---")
    print(response.headers)
    print(response.content)

print(status_codes._codes[response.status_code])


