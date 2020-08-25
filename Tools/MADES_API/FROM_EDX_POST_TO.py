#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     01.10.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import requests
#from EDX_MADES_client import EDXService
from EDX import create_client as EDXService
import argparse
import json
import time

# Example settings, these will be used if nothing else is defined

settings = dict(edx_server = "https://edx.entsoe.eu",
              edx_username = "",
              edx_password = "",
              post_headers = {'Content-Type': 'application/xml'},
             post_endpoint = 'http://example_rest_service.elering.ee',
           post_retry_time = 10,     # delay in seconds between retry
                post_retry = 3,      # number of times to retry
              edx_messages = ["RIMD", "EAD", "EPSD", "ESR", "CGMA-EXPORT-ALL"]
)


# Load deafult settings, if defined
settings_file_name = 'FROM_EDX_POST_TO.conf'
script_path = os.path.dirname(os.path.realpath(__file__))
settings_file = os.path.join(script_path, settings_file_name)


if os.path.exists(settings_file):
    with open(settings_file) as json_file:
        settings = json.load(json_file)
    print("Default settings loaded -> '{}'".format(settings_file))
else:
    print("No settings file present, loading defaults from code")


# Or define them when running the script for ENV parameters
parser = argparse.ArgumentParser()

# EDX parameters
parser.add_argument('--edx_server',     '-es',  help="base URL to EDX webserver, without port",                                                                 type= str,  default= settings["edx_server"])
parser.add_argument('--edx_username',   '-eu',  help="BasicAuth username for EDX webserver, if not implemented on EDX, then it is not needed",                  type= str,  default= settings["edx_username"])
parser.add_argument('--edx_password',   '-ep',  help="BasicAuth password for EDX webserver, if not implemented on EDX, then it is not needed",                  type= str,  default= settings["edx_password"])
parser.add_argument('--edx_messages',   '-em',  help="List of EDX message types to be forwarded. example: -em RIMD ESR EAD",                         nargs='+', type= str,  default= settings["edx_messages"])

# POST parameters
parser.add_argument('--post_endpoint',  '-pe',  help="POST endpoint full URL where the messages will be forwarded, basic auth can be added by using headers",   type= str,  default= settings["post_endpoint"])
parser.add_argument('--post_headers',   '-ph',  help="POST headers, could be used to implement BasicAuth",                                                      type= str,  default= settings["post_headers"])
parser.add_argument('--post_retry_time','-prt', help="Wait time between POST retry attempts",                                                                   type= int,  default= settings["post_retry_time"])
parser.add_argument('--post_retry',     '-pr',  help="Number of times to retry to POST",                                                                        type= int,  default= settings["post_retry"])


args = parser.parse_args()


# Process start

API = EDXService(args.edx_server, args.edx_username, args.edx_password)

for message_type in args.edx_messages:

    # Reset retry count
    retry_count = 0
    que_size    = 0


    test_message = API.receive_message(message_type)

    if test_message["receivedMessage"] != None:

        # Initial que size
        que_size  = test_message['remainingMessagesCount'] + 1

    print("Sending '{}' messages to {} -> que size = {}".format(message_type, args.post_endpoint, que_size))


    while que_size > 0 and retry_count <= args.post_retry:

        message  = API.receive_message(message_type)
        response = requests.post(args.post_endpoint, data=message["receivedMessage"]["content"], headers=args.post_headers)
        #print(response.text)


        if response.ok:
            API.confirm_received_message(message["receivedMessage"]["messageID"])
            que_size = message['remainingMessagesCount'] #Update que size
            print("Number of remaining messages {}".format(que_size))

        else:
            retry_count += 1
            print("WARNING - try {}/{} failed, trying again in {}s".format(retry_count, args.post_retry, args.post_retry_time))
            time.sleep(args.post_retry_time) #Lets try again


# If code ran here, the settings must have been OK, so lets save them for next use

with open(settings_file, 'w') as outfile:
    json.dump(args.__dict__, outfile, indent=4)