#-------------------------------------------------------------------------------
# Name:        EDX_MADES_client
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     27.03.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from __future__ import print_function

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport

import urllib3
urllib3.disable_warnings()

class EDXService():

    def __init__(self, server, username = "", password = "", debug = False):

        """At minimum server address or IP must be provided"""

        wsdl = '{}/ws/madesInWSInterface.wsdl'.format(server)

        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(username, password)

        transport = Transport(session = session)
        client = Client(wsdl, transport = transport)

        client.debug = debug

        self.service = client.create_service(
            '{http://mades.entsoe.eu/}MadesEndpointSOAP12',
            '{}/ws/madesInWSInterface'.format(server))


    def connectivity_test(self, reciver_EIC, business_type):
        """ConnectivityTest(receiverCode: xsd:string, businessType: xsd:string) -> messageID: xsd:string"""

        message_id = self.service.ConnectivityTest(reciver_EIC, business_type)

        return message_id

    def send_message(self, receiver_EIC, business_type, file_path, sender_EIC, message_id, converstaion_id):
        """SendMessage(message: ns0:SentMessage, conversationID: xsd:string) -> messageID: xsd:string
           ns0:SentMessage(receiverCode: xsd:string, businessType: xsd:string, content: xsd:base64Binary, senderApplication: xsd:string, baMessageID: xsd:string)"""

        loaded_file = open(file_path, "rb")
        file_text = loaded_file.read()

        message_dic = {"receiverCode": receiver_EIC, "businessType": business_type, "content": file_text, "senderApplication": sender_EIC, "baMessageID": message_id}
        message_id = self.service.SendMessage(message_dic, converstaion_id)

        return message_id

    def check_message_status(self, message_id):
        """CheckMessageStatus(messageID: xsd:string) -> messageStatus: ns0:MessageStatus
           ns0:MessageStatus(messageID: xsd:string, state: ns0:MessageState, receiverCode: xsd:string, senderCode: xsd:string, businessType: xsd:string, senderApplication: xsd:string, baMessageID: xsd:string, sendTimestamp: xsd:dateTime, receiveTimestamp: xsd:dateTime, trace: ns0:MessageTrace)"""

        status = self.service.CheckMessageStatus(message_id)
        return status

    def recieve_message(self, business_type, download_message=True):
        """ReceiveMessage(businessType: xsd:string, downloadMessage: xsd:boolean) -> receivedMessage: ns0:ReceivedMessage, remainingMessagesCount: xsd:long"""

        recieved_message = self.service.ReceiveMessage(business_type, download_message)

        return recieved_message

    def confirm_recieved_message(self, message_id):
        """ConfirmReceiveMessage(messageID: xsd:string) -> messageID: xsd:string"""

        message_id = self.service.ConfirmReceiveMessage(message_id)

        return message_id




# TEST

if __name__ == '__main__':

    server = "https://er-opdm.elering.sise"
    #server = "https://test-ba-opde.elering.sise"

    # Neede only if basic auth is set up for UI
    username = raw_input("UserName")
    password = raw_input("PassWord")

    service = EDXService(server, username, password, debug = True)

    #test_message_ID = service.send_message("10V000000000011Q", "RIMD", "C:/Users/kristjan.vilgo/Desktop/13681847.xml", "38V-EE-OPDM----S", "", "")
    #test_message_ID = service.send_message("10V1001A1001B106", "PEVF-EXPORT", r"C:\Users\kristjan.vilgo\Downloads\20190605_CGM_10V1001C--00012J_10V000000000011Q_A01_002.xml", "38V-EE-OPDM----S", "", "")

    test_message_ID = "deea65ad-a0a0-458b-b301-dccb0cf0d75f"

    status = service.check_message_status(test_message_ID)

##    test_message_ID = connectivity_test("38V-EE-OPDM----S", "")
##
##
##    print (status)
##    message = recieve_message("RIMD",1)
##    #confirm_recieved_message(message["receivedMessage"]["messageID"])


# SERVICE DESCRIPTION

##Operations:
##    CheckMessageStatus(messageID: xsd:string) -> messageStatus: ns0:MessageStatus
##    ConfirmReceiveMessage(messageID: xsd:string) -> messageID: xsd:string
##    ConnectivityTest(receiverCode: xsd:string, businessType: xsd:string) -> messageID: xsd:string
##    ReceiveMessage(businessType: xsd:string, downloadMessage: xsd:boolean) -> receivedMessage: ns0:ReceivedMessage, remainingMessagesCount: xsd:long
##    SendMessage(message: ns0:SentMessage, conversationID: xsd:string) -> messageID: xsd:string

##Global elements:
##     ns0:CheckMessageStatusError(errorCode: xsd:string, errorID: xsd:string, errorMessage: xsd:string, messageID: xsd:string, errorDetails: xsd:string)
##     ns0:CheckMessageStatusRequest(messageID: xsd:string)
##     ns0:CheckMessageStatusResponse(messageStatus: ns0:MessageStatus)
##     ns0:ConfirmReceiveMessageError(errorCode: xsd:string, errorID: xsd:string, errorMessage: xsd:string, messageID: xsd:string, errorDetails: xsd:string)
##     ns0:ConfirmReceiveMessageRequest(messageID: xsd:string)
##     ns0:ConfirmReceiveMessageResponse(messageID: xsd:string)
##     ns0:ConnectivityTestError(errorCode: xsd:string, errorID: xsd:string, errorMessage: xsd:string, receiverCode: xsd:string, errorDetails: xsd:string)
##     ns0:ConnectivityTestRequest(receiverCode: xsd:string, businessType: xsd:string)
##     ns0:ConnectivityTestResponse(messageID: xsd:string)
##     ns0:ReceiveMessageError(errorCode: xsd:string, errorID: xsd:string, errorMessage: xsd:string, businessType: xsd:string, errorDetails: xsd:string)
##     ns0:ReceiveMessageRequest(businessType: xsd:string, downloadMessage: xsd:boolean)
##     ns0:ReceiveMessageResponse(receivedMessage: ns0:ReceivedMessage, remainingMessagesCount: xsd:long)
##     ns0:SendMessageError(errorCode: xsd:string, errorID: xsd:string, errorMessage: xsd:string, receiverCode: xsd:string, errorDetails: xsd:string)
##     ns0:SendMessageRequest(message: ns0:SentMessage, conversationID: xsd:string)
##     ns0:SendMessageResponse(messageID: xsd:string)
##
##
##Global types:
##
##     ns0:MessageState
##     ns0:MessageStatus(messageID: xsd:string, state: ns0:MessageState, receiverCode: xsd:string, senderCode: xsd:string, businessType: xsd:string, senderApplication: xsd:string, baMessageID: xsd:string, sendTimestamp: xsd:dateTime, receiveTimestamp: xsd:dateTime, trace: ns0:MessageTrace)
##     ns0:MessageTrace(trace: ns0:MessageTraceItem[])
##     ns0:MessageTraceItem(timestamp: xsd:dateTime, state: ns0:MessageTraceState, component: xsd:string, componentDescription: xsd:string, details: xsd:string)
##     ns0:MessageTraceState
##     ns0:ReceivedMessage(messageID: xsd:string, receiverCode: xsd:string, senderCode: xsd:string, businessType: xsd:string, content: xsd:base64Binary, senderApplication: xsd:string, baMessageID: xsd:string)
##     ns0:SentMessage(receiverCode: xsd:string, businessType: xsd:string, content: xsd:base64Binary, senderApplication: xsd:string, baMessageID: xsd:string)




