#-------------------------------------------------------------------------------
# Name:        FROM_MADES_POST_TO
# Purpose:     Forward messages from MADES SOAP to REST via POST
#
# Author:      kristjan.vilgo
#
# Created:     10.02.2021
# Copyright:   (c) kristjan.vilgo 2021
# Licence:     GPL 2
#-------------------------------------------------------------------------------
import requests
import time


def confirm_delivery(mades_service, message):
    """Confirm message delivery and return remaining message count"""
    mades_service.confirm_received_message(message.receivedMessage.messageID)
    return message.remainingMessagesCount


def reque_message(mades_service, message, reque_endpoint="", reque_name="REQUE", reque_clean=False):
    """Put the current message back to a que"""

    # Clean the input que, if requested (Only works if que is at the same endpoint)
    if reque_clean:
        while True:
            reque_message = mades_service.receive_message(reque_name)

            if reque_message.receivedMessage.content is not None:
                mades_service.confirm_received_message(reque_message.receivedMessage.messageID)
                print(f"INFO - Removed {reque_name} with ID {reque_message.receivedMessage.messageID}")
            else:
                continue

    # Reque message
    message_id = mades_service.send_message(receiver_EIC=reque_endpoint,
                                            business_type=reque_name,
                                            content=message.receivedMessage.content)
    print(f"INFO - Message requed to {reque_name} with message ID {message_id}")


def request_and_post(mades_service, post_endpoint,
                     message_types_list=["*"],
                     continuous_process=False,
                     continuous_process_frequency=1,
                     post_headers={'Content-Type': 'application/xml'},
                     post_retry=0,
                     post_retry_time=3,
                     reque=False,
                     reque_endpoint="",
                     reque_name="REQUE",
                     reque_clean=False,
                     ):
    """Get Messages from ECP or EDX and post to defined address"""

    process = True
    while process:

        for message_type in message_types_list:

            # Reset retry count
            retry_count = 0
            que_size    = 0

            # MADES has the same que length in case of 0 on 1 message, test if content was provided with test query
            # Increase returned query count by one, if response was returned
            test_message = mades_service.receive_message(message_type)

            if test_message.receivedMessage is not None:

                # Initial que size
                que_size = test_message.remainingMessagesCount + 1

            # Do not print empty ques data in continuous process
            if (continuous_process and que_size > 0) or not continuous_process:
                print(f"INFO - Sending '{message_type}' messages to {post_endpoint} -> que size = {que_size}")

            # If there are messages in que or we are not trying send again
            while que_size > 0 and retry_count <= post_retry:

                # Get message form MADES service
                message = mades_service.receive_message(message_type)

                # Try to send to REST POST endpoint
                response = requests.post(post_endpoint, data=message.receivedMessage.content, headers=post_headers, verify=False)

                if response.ok:

                    # Confirm message and update que size
                    que_size = confirm_delivery(mades_service, message)
                    print(f"INFO - Number of remaining messages {que_size}")

                    # Put the message back to some que
                    if reque:
                        reque_message(mades_service, message, reque_endpoint, reque_name, reque_clean)

                # Lets try again to send to REST POST endpoint
                elif post_retry != 0:
                    print(f"WARNING - try {retry_count}/{post_retry} failed, trying again in {post_retry_time}s")
                    retry_count += 1
                    time.sleep(post_retry_time)

                # Remove failed unsent message and update que size
                else:
                    que_size = confirm_delivery(mades_service, message)
                    print("ERROR - Message delivery failed, removed from que")

        # Next run
        process = continuous_process
        time.sleep(continuous_process_frequency)

