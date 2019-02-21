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
from __future__ import print_function

from requests import Session
from zeep import Client
from zeep.transports import Transport

from lxml import etree

import os
import uuid

import json
import xmltodict

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #Used togehter with vei


WSDL_path = 'https://10.1.21.50:8443/cxf/OPDMSoapInterface?wsdl'

session = Session()
session.verify = False

transport = Transport(session = session)
client = Client(WSDL_path, transport = transport)
client.debug = True


API_VERSION = "0.1"


def get_element(element_path, xmltree):

    element = xmltree.find(element_path, namespaces = xmltree.nsmap)

    return element


def add_xml_elements(xml_string, parent_element_url, metadata_dict):

        xmltree = etree.fromstring(xml_string)
        metadata_element = get_element(parent_element_url, xmltree = xmltree)


        for key in metadata_dict:

            namespace, element_name = key.split(":")

            element_full_name = "{{{}}}{}".format(xmltree.nsmap[namespace], element_name)

            etree.SubElement(metadata_element, element_full_name, nsmap = xmltree.nsmap).text = metadata_dict[key]


        return etree.tostring(xmltree, pretty_print=True)


def execute_operation(operation_xml):
    """ExecuteOperation(payload: xsd:base64Binary) -> return: ns0:resultDto"""
    response = client.service.ExecuteOperation(operation_xml)
    return response

def publication_request(content_type, file_path_or_file_object):
    """PublicationRequest(dataset: ns0:opdeFileDto) -> return: ns0:resultDto,
    ns0:opdeFileDto(id: xsd:string, type: xsd:string, content: xsd:base64Binary)"""

    if type(file_path_or_file_object) == str:

        with open(file_path_or_file_object, "rb") as file_object:
            file_string = file_object.read()

        file_name =  os.path.basename(file_path_or_file_object)

    else:

        file_string = file_path_or_file_object.getvalue()
        file_name =  file_path_or_file_object.name


    payload = {"id": file_name, "type": content_type, "content": file_string}
    response = client.service.PublicationRequest(payload)

    return response



QueryObject  = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                <sm:Query xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                          xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                          xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                          xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                <sm:part name="name">{query_id}</sm:part>
                <sm:part name="query" type="opde:MetaDataPattern">
                    <opdm:OPDMObject>
                        <pmd:Object-Type>{object_type}</pmd:Object-Type>
                        <opde:Components/>
                        <opde:Dependencies/>
                    </opdm:OPDMObject>
                </sm:part>
                </sm:Query>"""



QueryProfile = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                <sm:Query xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                          xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                          xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                          xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                <sm:part name="name">{query_id}</sm:part>
                <sm:part name="query" type="opde:MetaDataPattern">
                    <opdm:Profile/>
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



def query_object(object_type="IGM", metadata_dict = "", components = [], dependencies = []):
    """objec_type ->IGM, CGM, BDS"""
    """metadata_dict_example = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00+01:00', 'pmd:timeHorizon': '1D'}"""
    """components_example = [{"opde:Component":"45955-94458-854789358-8557895"}, {"opde:Component":"45955-94458-854789358-8557895"}] """
    """dependencies_example = [{"opde:DependsOn":"45955-94458-854789358-8557895"}, {"opde:Supersedes":"45955-94458-854789358-8557895"}, {"opde:Replaces":"45955-94458-854789358-8557895"}] """

    query_id = "pyquery_{api_version}_{uuid}".format(uuid = uuid.uuid4(), api_version = API_VERSION)

    _QueryObject = QueryObject.format(query_id = query_id, object_type = object_type).encode()

    if metadata_dict != "":
        _QueryObject = add_xml_elements(_QueryObject, ".//opdm:OPDMObject", metadata_dict)

    for component in components:
        _QueryObject = add_xml_elements(_QueryObject, ".//opde:Components", component)

    for dependenci in dependencies:
        _QueryObject = add_xml_elements(_QueryObject, ".//opde:Dependencies", dependenci)

    #print(_QueryObject.decode())

    result = xmltodict.parse(etree.tostring(execute_operation(_QueryObject)), xml_attribs = False)



    return query_id, result


def query_profile(metadata_dict):

    """metadata_dict_example = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00+01:00', 'pmd:timeHorizon': '1D'}"""

    query_id = "pyquery_{api_version}_{uuid}".format(uuid = uuid.uuid4(), api_version = API_VERSION)

    _QueryProfile = QueryProfile.format(query_id = query_id).encode()
    _QueryProfile = add_xml_elements(_QueryProfile, ".//opdm:Profile", metadata_dict)

    #print(_QueryProfile.decode())

    result = xmltodict.parse(etree.tostring(execute_operation(_QueryProfile)), xml_attribs = False)


    return query_id, result


def get_content(content_id):

    new_GetContentResult = GetContentResult.format(content_id)
    #result = execute_operation(new_GetContentResult.encode())

    result = xmltodict.parse(etree.tostring(execute_operation(new_GetContentResult.encode())), xml_attribs = False)

    try:
        print("File downloded")
        print(result['sm:GetContentResult']['sm:part']['opdm:Profile']['opde:Content']) # Print url of the

    except:
        print("Error oqqoured")

    return result


def publication_list():

    result = execute_operation(PublicationsList.encode())
    return result


def publication_subscribe(subscription_id, publication_id, mode, metadata_list):
    """NOT IMPLEMENTED - IN DEVELOPMENT"""

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

    new_PublicationSubscriptionCancel.format(subscription_id)
    result = execute_operation(new_PublicationSubscriptionCancel)

    return result


# DEBUG
if __name__ == '__main__':
    #file_path  = select_file()[0]
    #file_path = "//elering.sise/teenused/NMM/data/ACG/Generated Cases/20180814T1830Z_ELERING_EQ_001.zip"
    #file_path = r"H:\20181206T2330Z_1D_CGMBA_SV_001.zip"
    #response = publication_request("CGMES", file_path)
    #print(etree.tostring(response, pretty_print = True).decode())
    #print(json.dumps(xmltodict.parse(etree.tostring(publication_list()), xml_attribs = False), indent = 4))
    #print(json.dumps(xmltodict.parse(etree.tostring(publication_list())), indent = 4))
    #metadata_dict = dict(TSO = "AST", cgmesProfile = "SV", validFrom = "20181024T1030Z")

    import pandas
    #metadata_dict = {"pmd:modelid":"c1860c13-7444-4d7f-a4fd-3eae2a360ce3"}
    #metadata_dict = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00+01:00', 'pmd:timeHorizon': '1D'}
    #response =   query_profile(metadata_dict)
    #print(json.dumps(response, indent = 4))
    #response['sm:QueryResult']['sm:part'].pop(0)
    #print(pandas.DataFrame(response['sm:QueryResult']['sm:part']))

    pandas.set_option("display.max_rows", 12)
    pandas.set_option("display.max_columns", 10)
    pandas.set_option("display.width", 1500)
    #pandas.set_option('display.max_colwidth', -1)


    query_id, response = query_object(object_type = "BDS", metadata_dict = {"opde:Context":"{'opde:IsOfficial': 'true'}"})

    list_of_responses = []

    for single_response in response['sm:QueryResult']['sm:part'][1:]:
        list_of_responses.append(single_response['opdm:OPDMObject'])

    data = pandas.DataFrame(list_of_responses)


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



 # SOAP API
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
