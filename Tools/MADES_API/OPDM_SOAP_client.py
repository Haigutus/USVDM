#-------------------------------------------------------------------------------
# Name:        OPDM_SOAP_client
# Purpose:      Expose OPDM functionality in python
#
# Author:      kristjan.vilgo
#
# Created:     31.07.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from requests import Session
from zeep import Client
from zeep.transports import Transport
import os
from lxml import etree

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #Used togehter with vei


from Tkinter import *
import ttk
from tkFileDialog import askopenfilename


WSDL_path = 'https://10.1.21.50:8443/cxf/OPDMSoapInterface?wsdl'

session = Session()
session.verify = False

transport = Transport(session = session)
client = Client(WSDL_path, transport = transport)
client.debug = True


def select_file(file_type='.*',dialogue_title="Select file"):
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

    print (filename)
    return [filename] #main function takes files in a list, thus single file must aslo be passed as list


def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):



        if filename.endswith(file_extension):
            #logging.info("Processing file:"+filename)
            matches.append(path + "//" + filename)
        else:
            print "Not a {} file: {}".format(file_extension, filename)
            #logging.warning("Not a {} file: {}".format(file_extension,file_text[0]))

    print matches
    return matches

def get_element(element_path, xmltree):

    element = xmltree.find(element_path, namespaces = xmltree.nsmap)

    return element


def execute_operation(operation_xml):
    """ExecuteOperation(payload: xsd:base64Binary) -> return: ns0:resultDto"""
    response = client.service.ExecuteOperation(operation_xml)

    if client.debug == True:

        print etree.tostring(response, pretty_print=True)

    return response

def publication_request(content_type, file_path):
    """PublicationRequest(dataset: ns0:opdeFileDto) -> return: ns0:resultDto,
    ns0:opdeFileDto(id: xsd:string, type: xsd:string, content: xsd:base64Binary)"""

    with open(file_path, "rb") as file_object:
        file_string = file_object.read()

    payload = {"id": os.path.basename(file_path), "type": content_type, "content": file_string}

    response = client.service.PublicationRequest(payload)

    return response


# Profile Meta example
"""
<pmd:fileName>20181024T1030Z_EMS_EQ_000.XML</pmd:fileName>
<pmd:modelid>6bfa5c34-f4fb-45f3-a909-1ae94c08d4e3</pmd:modelid>
<pmd:versionNumber>000</pmd:versionNumber>
<pmd:content-reference>CGMES/1D/EMS/20181024/103000/EQ/20181024T1030Z_EMS_EQ_000.XML</pmd:content-reference>
<pmd:isFullModel>true</pmd:isFullModel>
<pmd:timeHorizon>1D</pmd:timeHorizon>
<pmd:modelPartReference>EMS</pmd:modelPartReference>
<pmd:contentType>CGMES</pmd:contentType>
<pmd:conversationId>18240149</pmd:conversationId>
<pmd:description>Created by Transmission Network Analyzer 2.3</pmd:description>
<pmd:creationDate>2018-10-24T12:58:23.000Z</pmd:creationDate>
<pmd:TSO>EMS</pmd:TSO>
<pmd:cgmesProfile>EQ</pmd:cgmesProfile>
<pmd:modelingAuthoritySet>https://ems.rs/OperationalPlanning</pmd:modelingAuthoritySet>
<pmd:version>0</pmd:version>
<pmd:scenarioDate>2018-10-24T10:30:00.000Z</pmd:scenarioDate>
<pmd:validFrom>20181024T1030Z</pmd:validFrom>
<pmd:modelProfile>http://entsoe.eu/CIM/EquipmentCore/3/1</pmd:modelProfile>
<pmd:fullModel_ID>6bfa5c34-f4fb-45f3-a909-1ae94c08d4e3</pmd:fullModel_ID>
"""


QueryObject  = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                <sm:Query xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                          xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                          xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                          xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                <sm:part name="name">{}</sm:part>
                <sm:part name="query" type="opde:MetaDataPattern">
                    <opdm:OPDMObject>
                        <pmd:Object-Type>{}</pmd:Object-Type>
                    </opdm:OPDMObject>
                </sm:part>
                </sm:Query>"""



QueryProfile = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                <sm:Query xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                          xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                          xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                          xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                <sm:part name="name">py_query</sm:part>
                <sm:part name="query" type="opde:MetaDataPattern">
                    <opdm:Profile>

                    </opdm:Profile>
                </sm:part>
            </sm:Query>"""


GetContentResult = """<?xml version="1.0" encoding="UTF-8"?>
                            <sm:GetContent xmlns="http://entsoe.eu/opde/ServiceModel/1/0"
                                           xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                                           xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                                           xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                                <sm:part name="identifier" type="opde:ShortMetaData">
                                    <opdm:Profile>
                                        <opde:Id>{}</opde:Id>
                                    </opdm:Profile>
                                    </sm:part>
                            </sm:GetContent>"""


PublicationsList = """<?xml version="1.0" encoding="UTF-8"?>
                              <sm:PublicationsSubscriptionList xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0">
                                    <sm:part name="listType">AVAILABLE_PUBLICATIONS</sm:part>
                              </sm:PublicationsSubscriptionList>"""




PublicationSubscriptionCancel = """<sm:PublicationSubscriptionCancel xmlns="http://entsoe.eu/opde/ServiceModel/1/0"
                                                                        xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                                                                        xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                                                                        xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                                                                        xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                                            <sm:part name="subscriptionID">{}</sm:part>
                                        </sm:PublicationSubscriptionCancel>"""

def add_profile_metadata(xml_string, parent_element_url, metadata_dict):

        xmltree = etree.fromstring(xml_string)
        metadata_element = get_element(parent_element_url, xmltree = xmltree)


        for key in metadata_dict:

            element_name = "{{{}}}{}".format(xmltree.nsmap["pmd"], key)

            etree.SubElement(metadata_element, element_name, nsmap = xmltree.nsmap).text = metadata_dict[key]


        return etree.tostring(xmltree, pretty_print=True)


def query_object(object_type, query_name = "py_query"):
    """objec_type ->IGM, CGM, BDS"""

    new_QueryObject = QueryObject.format(query_name, object_type)
    result = execute_operation(new_QueryObject)

    return result


def query_profile(metadata_dict):


    new_QueryProfile = add_profile_metadata(QueryProfile, ".//opdm:Profile", metadata_dict)

    result = execute_operation(new_QueryProfile)

    return result


def get_content(content_id):

    new_GetContentResult = GetContentResult.format(content_id)
    result = execute_operation(new_GetContentResult)

    #print result
    return result


def publication_list():

    result = execute_operation(PublicationsList)
    return result


def publication_subscribe(subscription_id, publication_id, mode, metadata_list):

    PublicationSubscribe = """<sm:PublicationSubscribe xmlns="http://entsoe.eu/opde/ServiceModel/1/0"
                                xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                                xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                                xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                                xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                                <sm:part name="subscriptionID">subscription-1000</sm:part>
                                <sm:part name="publicationID">ENTSOE-OPDM-Publish-CGM</sm:part>
                                <sm:part name="mode">DIRECT_CONTENT</sm:part>
                                <sm:part name="pattern" type="opde:MetaDataPattern">
                                    <opdm:OPDMObject>
                                        <pmd:Object-Type>CGM</pmd:Object-Type>
                                        <pmd:timeHorizon>1D</pmd:timeHorizon>
                                    </opdm:OPDMObject>
                                    </sm:part>
                                </sm:PublicationSubscribe>"""


def publication_cancel_subscription(subscription_id):

    PublicationSubscriptionCancel.format(subscription_id)
    result = execute_operation(PublicationSubscriptionCancel)

    return result



##if __name__ == '__main__':
##    #file_path  = select_file()[0]
##    #file_path = "//elering.sise/teenused/NMM/data/ACG/Generated Cases/20180730T1830Z_ELERING_EQ_001.zip"
##    #response = publication_request("CGMES", file_path)
##
##    opdm_query ="""<sm:Query xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
##                      xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
##                        xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
##                        xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
##                        <sm:part name="name">BDSQuery</sm:part>
##                        <sm:part name="query" type="opde:MetaDataPattern">
##                            <opdm:OPDMObject>
##                                 <pmd:Object-Type>BDS</pmd:Object-Type>
##                           </opdm:OPDMObject>
##                       </sm:part>
##                    </sm:Query>"""
##
##
##    test = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
##                <sm:Query xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
##                          xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
##                          xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
##                            xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
##                    <sm:part name="name">IGM test query</sm:part>
##                    <sm:part name="query" type="opde:MetaDataPattern">
##                        <opdm:OPDMObject>
##                                 <pmd:Object-Type>IGM</pmd:Object-Type>
##                        </opdm:OPDMObject>
##                        <opdm:Profile>
##                            <pmd:cgmesProfile>EQ</pmd:cgmesProfile>
##                            <pmd:scenarioDate>2017-10-05</pmd:scenarioDate>
##                            <opde:Dependencies>
##                            </opde:Dependencies>
##                        </opdm:Profile>
##                    </sm:part>
##                </sm:Query>"""
##
##
##
##
##
##    result = execute_operation(opdm_query)
##
##    #print etree.tostring(results, pretty_print=True)


metadata_dict = dict(TSO = "AST", cgmesProfile = "SV", validFrom = "20181024T1030Z")


test_xml_1 = """<sm:GetContentResult xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0" xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0" xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0" xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0" xmlns:ns2="http://soap.interfaces.application.components.opdm.entsoe.eu/" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" opdm-version="2.5.0.878">
  <sm:part name="content" type="opde:DataSet">
    <opdm:Profile>
      <opde:Id>5d9c9d99-933d-432e-b096-a307eaa1c140</opde:Id>
      <opde:Dependencies/>
      <pmd:fileName>20160710T0000Z_ENTSO-E_EQ_BD_001.xml</pmd:fileName>
      <pmd:cgmesProfile>EQ_BD</pmd:cgmesProfile>
      <pmd:modelid>5d9c9d99-933d-432e-b096-a307eaa1c140</pmd:modelid>
      <pmd:isFullModel>true</pmd:isFullModel>
      <pmd:timeHorizon>1D</pmd:timeHorizon>
      <pmd:fullModel_ID>5d9c9d99-933d-432e-b096-a307eaa1c140</pmd:fullModel_ID>
      <pmd:contentType>CGMES</pmd:contentType>
      <pmd:creationDate>2018-07-10T07:55:23.547Z</pmd:creationDate>
      <pmd:description>Official CGM boundary set</pmd:description>
      <pmd:modelPartReference>ENTSO-E</pmd:modelPartReference>
      <pmd:modelingAuthoritySet>http://tscnet.eu/EMF</pmd:modelingAuthoritySet>
      <pmd:validFrom>20160710T0000Z</pmd:validFrom>
      <pmd:scenarioDate>2016-07-10T00:00:00.000Z</pmd:scenarioDate>
      <pmd:version>1</pmd:version>
      <pmd:conversationId>594197046</pmd:conversationId>
      <pmd:content-reference>CGMES/1D/ENTSO-E/20160710/00000/EQ_BD/20160710T0000Z_ENTSO-E_EQ_BD_001.xml</pmd:content-reference>
      <pmd:modelProfile>http://entsoe.eu/CIM/EquipmentBoundaryOperation/3/1</pmd:modelProfile>
      <pmd:versionNumber>001</pmd:versionNumber>
      <opde:Dependencies/>
      <opde:Content sm:uri="20160710T0000Z_ENTSO-E_EQ_BD_001.xml">/opt/opdm-home/opdm-client/./opdm/operation-client/local-storage/20160710T0000Z_ENTSO-E_EQ_BD_001.xml</opde:Content>
    </opdm:Profile>
  </sm:part>
</sm:GetContentResult>"""



"""
Prefixes:
     ns0: http://soap.interfaces.application.components.opdm.entsoe.eu/
     xsd: http://www.w3.org/2001/XMLSchema

Global elements:
     ns0:ExecuteOperation(ns0:ExecuteOperation)
     ns0:ExecuteOperationResponse(ns0:ExecuteOperationResponse)
     ns0:PublicationRequest(ns0:PublicationRequest)
     ns0:PublicationRequestResponse(ns0:PublicationRequestResponse)
     ns0:opde-file(ns0:opdeFileDto)


Global types:

     ns0:ExecuteOperation(payload: xsd:base64Binary)
     ns0:ExecuteOperationResponse(return: ns0:resultDto)
     ns0:PublicationRequest(dataset: ns0:opdeFileDto)
     ns0:PublicationRequestResponse(return: ns0:resultDto)
     ns0:opdeFileDto(id: xsd:string, type: xsd:string, content: xsd:base64Binary)
     ns0:resultDto(_value_1: ANY)
     xsd:ENTITIES
     xsd:ENTITY
     xsd:ID
     xsd:IDREF
     xsd:IDREFS
     xsd:NCName
     xsd:NMTOKEN
     xsd:NMTOKENS
     xsd:NOTATION
     xsd:Name
     xsd:QName
     xsd:anySimpleType
     xsd:anyURI
     xsd:base64Binary
     xsd:boolean
     xsd:byte
     xsd:date
     xsd:dateTime
     xsd:decimal
     xsd:double
     xsd:duration
     xsd:float
     xsd:gDay
     xsd:gMonth
     xsd:gMonthDay
     xsd:gYear
     xsd:gYearMonth
     xsd:hexBinary
     xsd:int
     xsd:integer
     xsd:language
     xsd:long
     xsd:negativeInteger
     xsd:nonNegativeInteger
     xsd:nonPositiveInteger
     xsd:normalizedString
     xsd:positiveInteger
     xsd:short
     xsd:string
     xsd:time
     xsd:token
     xsd:unsignedByte
     xsd:unsignedInt
     xsd:unsignedLong
     xsd:unsignedShort

Bindings:
     Soap11Binding: {http://opde.entsoe.eu/opdm/Message#v1}OPDMSoapInterfaceSoapBinding

Service: OPDMSoapInterface
     Port: OPDMSoapInterfacePort (Soap11Binding: {http://opde.entsoe.eu/opdm/Message#v1}OPDMSoapInterfaceSoapBinding)
         Operations:
            ExecuteOperation(payload: xsd:base64Binary) -> return: ns0:resultDto
            PublicationRequest(dataset: ns0:opdeFileDto) -> return: ns0:resultDto
"""