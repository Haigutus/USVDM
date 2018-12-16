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
from requests import Session
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from zeep import Client
from zeep.transports import Transport
import base64
from lxml import etree
from Tkinter import *
import ttk
from tkFileDialog import askdirectory
from tkFileDialog import askopenfilename


WSDL_path = 'http://10.1.21.50:9090/ws/madesInWSInterface.wsdl'

session = Session()
session.auth = HTTPBasicAuth("elering", "elering.edx")

transport = Transport(session = session)
client = Client(WSDL_path, transport = transport)

#client.debug = True


service = client.create_service(
    '{http://mades.entsoe.eu/}MadesEndpointSOAP12',
    'http://10.1.21.50:9090/ws/madesInWSInterface')



def connectivity_test(reciver_EIC, business_type):
    """ConnectivityTest(receiverCode: xsd:string, businessType: xsd:string) -> messageID: xsd:string"""
    message_id = service.ConnectivityTest(reciver_EIC, business_type)
    return message_id

def send_message(receiver_EIC, business_type, file_path, sender_EIC, message_id, converstaion_id):
    """SendMessage(message: ns0:SentMessage, conversationID: xsd:string) -> messageID: xsd:string
       ns0:SentMessage(receiverCode: xsd:string, businessType: xsd:string, content: xsd:base64Binary, senderApplication: xsd:string, baMessageID: xsd:string)"""

    loaded_file = open(file_path, "r")
    file_text = loaded_file.read()
    message_dic = {"receiverCode": receiver_EIC, "businessType": business_type, "content": base64.b64encode(file_text), "senderApplication": sender_EIC, "baMessageID": message_id}
    message_id = service.SendMessage(message_dic, converstaion_id)
    return message_id

def check_message_status(message_id):
    """CheckMessageStatus(messageID: xsd:string) -> messageStatus: ns0:MessageStatus
       ns0:MessageStatus(messageID: xsd:string, state: ns0:MessageState, receiverCode: xsd:string, senderCode: xsd:string, businessType: xsd:string, senderApplication: xsd:string, baMessageID: xsd:string, sendTimestamp: xsd:dateTime, receiveTimestamp: xsd:dateTime, trace: ns0:MessageTrace)"""

    status = service.CheckMessageStatus(message_id)
    return status

def recieve_message(business_type, number_of_files_to_download):
    """ReceiveMessage(businessType: xsd:string, downloadMessage: xsd:boolean) -> receivedMessage: ns0:ReceivedMessage, remainingMessagesCount: xsd:long"""
    recieved_message_raw = service.ReceiveMessage(business_type, number_of_files_to_download)

    recieved_message_dict = recieved_message_raw._root
    recieved_message_dict["receivedMessage"]["content"] = recieved_message_raw.attachments[0].content

    return recieved_message_dict

def confirm_recieved_message(message_id):
    """ConfirmReceiveMessage(messageID: xsd:string) -> messageID: xsd:string"""
    message_id = service.ConfirmReceiveMessage(message_id)
    return message_id

def select_file(file_type='.*',dialogue_title="Select file"):
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

    print filename
    return [filename] #main function takes files in a list, thus single file must aslo be passed as list


# TEST

if __name__ == '__main__':

    client.debug = True

##    test_message_ID = connectivity_test("38V-EE-OPDM----S", "")
##
    test_message_ID = send_message("10V000000000011Q", "RIMD", "C:/Users/kristjan.vilgo/Desktop/13681847.xml", "38V-EE-OPDM----S", "", "")

    status = check_message_status(test_message_ID)
##
##    print status

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




