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

import requests
import EDX_MADES_client as API

headers = {'Content-Type': 'application/xml'}
post_url = 'http://er-bht-arendus.elering.sise/service/index.php'

que_size = 1
retry_time = 10

message_type_list = ["RIMD", "EAD", "EPSD", "ESR"]


for message_type in message_type_list:

    que_size = API.recieve_message(message_type,1)['remainingMessagesCount'] # Initial que size

    print("Sending {} messages to {} -> que size = {}".format(message_type, post_url, que_size))

    while que_size > 0:

        message = API.recieve_message(message_type,1)



        if que_size == 0:
            continue

        response = requests.post(post_url, data=message["receivedMessage"]["content"], headers=headers)

        print(response.text)
        print(requests.status_codes._codes[response.status_code] )

        if response.status_code == 202:
            API.confirm_recieved_message(message["receivedMessage"]["messageID"])
            que_size = API.recieve_message(message_type,1)['remainingMessagesCount'] #Update que size

        else:
            time.sleep(retry_time) #Lets try again

