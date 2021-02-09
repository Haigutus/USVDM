#-------------------------------------------------------------------------------
# Name:        FROM_ECP_POST_TO
# Purpose:     Forward messages from ECP to REST endpoint via POST
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
from ECP_MADES_client import create_client as ECPService
import argparse
import json
import time

# Example settings, these will be used if nothing else is defined

settings = dict(ecp_server="https://ecp.entsoe.eu",
                ecp_username="",
                ecp_password="",
                post_headers={'Content-Type': 'application/xml'},
                post_endpoint='http://example_rest_service.elering.ee',
                post_retry_time=10,     # delay in seconds between retry
                post_retry=0,      # number of times to retry
                ecp_messages=["RIMD", "EAD", "EPSD", "ESR", "CGMA-EXPORT-ALL"],
                continuous_process=False,
                continuous_process_frequency=1

)


# ENV parameters
parser = argparse.ArgumentParser()

# ecp parameters
parser.add_argument('--ecp_server',     '-es',  help="base URL to ecp webserver, without port",                                                                 type=str,  default=settings["ecp_server"])
parser.add_argument('--ecp_username',   '-eu',  help="BasicAuth username for ecp webserver, if not implemented on ecp, then it is not needed",                  type=str,  default=settings["ecp_username"])
parser.add_argument('--ecp_password',   '-ep',  help="BasicAuth password for ecp webserver, if not implemented on ecp, then it is not needed",                  type=str,  default=settings["ecp_password"])
parser.add_argument('--ecp_messages',   '-em',  help="List of ecp message types to be forwarded. example: -em RIMD ESR EAD",                         nargs='+', type=str,  default=settings["ecp_messages"])

# POST parameters
parser.add_argument('--post_endpoint',  '-pe',  help="POST endpoint full URL where the messages will be forwarded, basic auth can be added by using headers",   type=str,  default=settings["post_endpoint"])
parser.add_argument('--post_headers',   '-ph',  help="POST headers, could be used to implement BasicAuth, string '{'Content-Type': 'application/xml'}'",        type=json.loads,  default=settings["post_headers"])
parser.add_argument('--post_retry_time','-prt', help="Wait time between POST retry attempts [s] int",                                                           type=int,  default=settings["post_retry_time"])
parser.add_argument('--post_retry',     '-pr',  help="Number of times to retry to POST",                                                                        type=int,  default=settings["post_retry"])

# Continuous process
parser.add_argument('--continuous_process',           '-cp',    help="If the process should run continuously, no parameters expected",                          default=settings["continuous_process"], action='store_true')
parser.add_argument('--continuous_process_frequency', '-cpf',   help="If continuous process is enabeled, how often it should run [s] float",                    type=float,default=settings["continuous_process_frequency"])

args = parser.parse_args()

#print(args)  # DEBUG

# TODO maybe we could add reque, meaning send same message to the end of que


# Process start

API = ECPService(args.ecp_server, args.ecp_username, args.ecp_password)
process = True
while process:

    for message_type in args.ecp_messages:

        # Reset retry count
        retry_count = 0
        que_size    = 0


        test_message = API.receive_message(message_type)

        if test_message["receivedMessage"] != None:

            # Initial que size
            que_size = test_message['remainingMessagesCount'] + 1

        if (args.continuous_process and que_size > 0) or not args.continuous_process:

            print("INFO - Sending '{}' messages to {} -> que size = {}".format(message_type, args.post_endpoint, que_size))

        while que_size > 0 and retry_count <= args.post_retry:

            message  = API.receive_message(message_type)
            response = requests.post(args.post_endpoint, data=message["receivedMessage"]["content"].decode(), headers=args.post_headers)
            #print(response.text)


            if response.ok:
                API.confirm_received_message(message["receivedMessage"]["messageID"])
                que_size = message['remainingMessagesCount'] #Update que size
                print("INFO - Number of remaining messages {}".format(que_size))

            elif args.post_retry != 0:
                retry_count += 1
                print("WARNING - try {}/{} failed, trying again in {}s".format(retry_count, args.post_retry, args.post_retry_time))
                time.sleep(args.post_retry_time) #Lets try again

            else:
                API.confirm_received_message(message["receivedMessage"]["messageID"])
                que_size = message['remainingMessagesCount'] #Update que size
                print("ERROR - Message delivery failed, removed from que")

    # Next run
    process = args.continuous_process
    time.sleep(args.continuous_process_frequency)
