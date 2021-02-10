#-------------------------------------------------------------------------------
# Name:        FROM_MADES_POST_TO_CLI
# Purpose:     Command Line interface to forward messages from MADES SOAP API to REST endpoint via POST
#
# Author:      kristjan.vilgo
#
# Created:     01.10.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import EDX_MADES_client, ECP_MADES_client, FROM_MADES_POST_TO
import argparse
import json

service_mapping = {"EDX": EDX_MADES_client,
                   "ECP": ECP_MADES_client}


# ENV parameters
parser = argparse.ArgumentParser()

# MADES parameters
parser.add_argument('--server',       '-s',   help="base URL to MADES webserver, without port",                                                                 type=str, required=True)
parser.add_argument('--service_type', '-st', help="The type of service",                                                                                        type=str,               default="EDX", choices=["ECP, EDX"])
parser.add_argument('--username',     '-eu',  help="BasicAuth username for MADES webserver, if not implemented on MADES, then it is not needed",                type=str,               default="")
parser.add_argument('--password',     '-ep',  help="BasicAuth password for MADES webserver, if not implemented on MADES, then it is not needed",                type=str,               default="")
parser.add_argument('--messages',     '-em',  help="List of MADES message types to be forwarded. example: -em RIMD ESR EAD",                                    nargs='+', type=str,    default=["*"])

# POST parameters
parser.add_argument('--post_endpoint',   '-pe',  help="POST endpoint full URL where the messages will be forwarded, basic auth can be added by using headers",  type=str, required=True)
parser.add_argument('--post_headers',    '-ph',  help="POST headers, could be used to implement BasicAuth, string '{'Content-Type': 'application/xml'}'",       type=json.loads,        default={'Content-Type': 'application/xml'})
parser.add_argument('--post_retry_time', '-prt', help="Wait time between POST retry attempts [s] int",                                                          type=int,               default=10)
parser.add_argument('--post_retry',      '-pr',  help="Number of times to retry to POST",                                                                       type=int,               default=0)

# Continuous process
parser.add_argument('--continuous_process',           '-cp',    help="If the process should run continuously, no parameters expected",                                                  default=False, action='store_true')
parser.add_argument('--continuous_process_frequency', '-cpf',   help="If continuous process is enabeled, how often it should run [s] float",                    type=float,             default=1)

# Reque
parser.add_argument('--reque',          '-rq',   help="If the process should run continuously, no parameters expected",                                                                 default=False, action='store_true')
parser.add_argument('--reque_endpoint', '-re',   help="If continuous process is enabeled, how often it should run [s] float",                                   type=str,               default="")
parser.add_argument('--reque_name',     '-rn',   help="If the process should run continuously, no parameters expected",                                         type=str,               default="REQUE")
parser.add_argument('--reque_clean',    '-rc',   help="If continuous process is enabeled, how often it should run [s] float",                                                           default=False, action='store_true')

args = parser.parse_args()

print(args)  # DEBUG


# Create Service
mades_service = service_mapping[args.service_type].create_client(args.server, args.username, args.password)

# Run Process
FROM_MADES_POST_TO.request_and_post(mades_service,
                                    args.post_endpoint,
                                    args.messages,
                                    args.continious_process,
                                    args.continious_process_frequency,
                                    args.reque,
                                    args.reque_endpoint,
                                    args.reque_name,
                                    args.reque_clean)

