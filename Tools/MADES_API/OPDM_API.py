#-------------------------------------------------------------------------------
# Name:        OPDM_API
# Purpose:     Expose OPDM functionality in python
#
# Author:      kristjan.vilgo
#
# Created:     31.07.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     GPL2
#-------------------------------------------------------------------------------
from __future__ import print_function

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport

from lxml import etree

import os
import uuid

import json
import xmltodict

import urllib3
urllib3.disable_warnings()


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


class OPDMservice():

    def __init__(self, server, username = "", password = "", debug = False):

        """At minimum server address or IP must be provided
        service = OPDMservice(<server_ip_or_address>)"""

        wsdl = '{}/cxf/OPDMSoapInterface?wsdl'.format(server)

        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(username, password)

        transport = Transport(session = session)
        client = Client(wsdl, transport = transport)
        client.debug = debug

        self.client = client
        self.API_VERSION = "0.2"


    class operations:

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





    def execute_operation(self, operation_xml):
        """ExecuteOperation(payload: xsd:base64Binary) -> return: ns0:resultDto"""
        response = self.client.service.ExecuteOperation(operation_xml)
        return response

    def publication_request(self, content_type, file_path_or_file_object):
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
        response = self.client.service.PublicationRequest(payload)

        return response





    def query_object(self, object_type="IGM", metadata_dict = "", components = [], dependencies = []):
        """objec_type ->IGM, CGM, BDS"""
        """metadata_dict_example = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00+01:00', 'pmd:timeHorizon': '1D'}"""
        """components_example = [{"opde:Component":"45955-94458-854789358-8557895"}, {"opde:Component":"45955-94458-854789358-8557895"}] """
        """dependencies_example = [{"opde:DependsOn":"45955-94458-854789358-8557895"}, {"opde:Supersedes":"45955-94458-854789358-8557895"}, {"opde:Replaces":"45955-94458-854789358-8557895"}] """

        query_id = "pyquery_{api_version}_{uuid}".format(uuid = uuid.uuid4(), api_version = self.API_VERSION)

        _QueryObject = self.operations.QueryObject.format(query_id = query_id, object_type = object_type).encode()

        if metadata_dict != "":
            _QueryObject = add_xml_elements(_QueryObject, ".//opdm:OPDMObject", metadata_dict)

        for component in components:
            _QueryObject = add_xml_elements(_QueryObject, ".//opde:Components", component)

        for dependenci in dependencies:
            _QueryObject = add_xml_elements(_QueryObject, ".//opde:Dependencies", dependenci)

        #print(_QueryObject.decode())

        result = xmltodict.parse(etree.tostring(self.execute_operation(_QueryObject)), xml_attribs = False)



        return query_id, result


    def query_profile(self, metadata_dict):

        """metadata_dict_example = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00', 'pmd:timeHorizon': '1D'}"""

        query_id = "pyquery_{api_version}_{uuid}".format(uuid = uuid.uuid4(), api_version = self.API_VERSION)

        _QueryProfile = self.operations.QueryProfile.format(query_id = query_id).encode()
        _QueryProfile = add_xml_elements(_QueryProfile, ".//opdm:Profile", metadata_dict)

        #print(_QueryProfile.decode())

        result = xmltodict.parse(etree.tostring(self.execute_operation(_QueryProfile)), xml_attribs = False)


        return query_id, result


    def get_content(self, content_id):

        new_GetContentResult = self.operations.GetContentResult.format(content_id)
        #result = execute_operation(new_GetContentResult.encode())

        result = xmltodict.parse(etree.tostring(self.execute_operation(new_GetContentResult.encode())), xml_attribs = False)

        try:
            print("File downloded")
            print(result['sm:GetContentResult']['sm:part']['opdm:Profile']['opde:Content']) # Print url of the

        except:
            print("Error oqqoured")

        return result


    def publication_list(self):

        result = self.execute_operation(self.operations.PublicationsList.encode())
        return result


    def publication_subscribe(subscription_id, publication_id, mode, metadata_list):
        """NOT IMPLEMENTED"""

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


    def publication_cancel_subscription(self, subscription_id):
        """Cancel subscription by subscription ID"""

        new_PublicationSubscriptionCancel = self.operations.PublicationSubscriptionCancel.format(subscription_id)
        result = self.execute_operation(new_PublicationSubscriptionCancel)

        return result


# DEBUG
if __name__ == '__main__':


    server = 'https://test-ba-opde.elering.sise:8443'
    service = OPDMservice(server, debug=False)


    # Query model part example

##    # Available profile meta
##    """
##    "pmd:content-reference": "CGMES/1D/ELERING/20190712/93000/SV/20190712T0930Z_1D_ELERING_SV_001.zip",
##    "pmd:conversationId": "-581868906",
##    "pmd:fileName": "20190712T0930Z_1D_ELERING_SV_001.zip",
##    "pmd:isFullModel": "true",
##    "pmd:TSO": "ELERING",
##    "pmd:modelingAuthoritySet": "http://www.elering.ee/OperationalPlanning",
##    "pmd:timeHorizon": "1D",
##    "pmd:contentType": "CGMES",
##    "pmd:modelProfile": "http://entsoe.eu/CIM/StateVariables/4/1",
##    "pmd:validFrom": "20190712T0930Z",
##    "pmd:modelid": "3c09a995-d250-460d-9b34-09f75fc2cade",
##    "pmd:creationDate": "2019-07-11T18:16:46Z",
##    "pmd:cgmesProfile": "SV",
##    "pmd:version": "001",
##    "pmd:fullModel_ID": "3c09a995-d250-460d-9b34-09f75fc2cade",
##    "pmd:modelPartReference": "ELERING",
##    "pmd:description": "ELERING AP--Base-Network",
##    "pmd:profileSize": "1282790",
##    "pmd:scenarioDate": "2019-07-12T09:30:00Z",
##    "pmd:versionNumber": "001"
##    """
##
##
##    metadata_dict = {'pmd:scenarioDate': '2019-07-12T09:30:00', 'pmd:timeHorizon': '1D', 'pmd:cgmesProfile': 'SV'}
##
##    message_id, response = service.query_profile(metadata_dict)
##    print(json.dumps(response, indent = 4))
##
##    # Create nice table view
##    import pandas
##    pandas.set_option("display.max_rows", 12)
##    pandas.set_option("display.max_columns", 10)
##    pandas.set_option("display.width", 1500)
##    #pandas.set_option('display.max_colwidth', -1)

##    response['sm:QueryResult']['sm:part'].pop(0)
##    print(pandas.DataFrame(response['sm:QueryResult']['sm:part']))


    # Model submission example

##    file_path = r"\\elering.sise\teenused\NMM\data\ACG\Generated Cases Archive\20190713T1530Z__ELERING_EQ_001.zip"
##    response = service.publication_request("CGMES", file_path)
##    print(etree.tostring(response, pretty_print = True).decode())


    # Publication list example

##    response = service.publication_list()
##    print(json.dumps(xmltodict.parse(etree.tostring(response), xml_attribs = False), indent = 4))
##    #print(json.dumps(xmltodict.parse(etree.tostring(publication_list())), indent = 4))


    # Query model example

##    query_id, response = service.query_object(object_type = "BDS", metadata_dict = {"opde:Context":"{'opde:IsOfficial': 'true'}"})
##
##    list_of_responses = []
##
##    for single_response in response['sm:QueryResult']['sm:part'][1:]:
##        list_of_responses.append(single_response['opdm:OPDMObject'])
##
##    Create nice table view
##    import pandas
##    pandas.set_option("display.max_rows", 12)
##    pandas.set_option("display.max_columns", 10)
##    pandas.set_option("display.width", 1500)
##    #pandas.set_option('display.max_colwidth', -1)
##
##    data = pandas.DataFrame(list_of_responses)


    # Get content example

##    model_or_modelpart_UUID = "3c09a995-d250-460d-9b34-09f75fc2cade"
##    response = service.get_content()
##    print(json.dumps(response, indent = 4))
##    print(response['sm:GetContentResult']['sm:part']['opdm:Profile']['opde:Content'])







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
