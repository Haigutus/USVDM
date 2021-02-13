#-------------------------------------------------------------------------------
# Name:        OPDM_SOAP_API
# Purpose:     Expose OPDM functionality in python
#
# Author:      kristjan.vilgo
#
# Created:     31.07.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     GPL2
#-------------------------------------------------------------------------------
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
from zeep.plugins import HistoryPlugin

from lxml import etree
from lxml.builder import ElementMaker

import os
import uuid

import json
import xmltodict

from datetime import datetime, timezone
import aniso8601

import urllib3



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


def xml_to_dict(xml_tree, xml_atrribs = False):

    xml_string = etree.tostring(xml_tree)
    xml_dict = xmltodict.parse(xml_string, xml_attribs = xml_atrribs)


class OPDMservice():

    def __init__(self, server, username="", password="", debug=False, verify=False):

        """At minimum server address or IP must be provided
        service = OPDMservice(<server_ip_or_address>)"""

        self.debug = debug
        self.history = HistoryPlugin()
        self.API_VERSION = "0.3"

        service_wsdl = '{}/cxf/OPDMSoapInterface?wsdl'.format(server)
        auth_wsdl = '{}/cxf/OPDMSoapInterface/SoapAuthentication?wsdl'.format(server)

        session = Session()

        # Use this only for testing, correct way is to add OPDM certs to trust store
        if not verify:
            urllib3.disable_warnings()
            session.verify = False

        # Set up client
        if debug:
            self.client = Client(service_wsdl, transport=Transport(session=session), plugins=[self.history])
        else:
            self.client = Client(service_wsdl, transport=Transport(session=session))

        # Set up auth
        if username == "":
            self.auth = False
        elif debug:
            self.auth = True
            self.auth_client = Client(auth_wsdl, transport=Transport(session=session),  wsse=UsernameToken(username, password=password), plugins=[self.history])
            self.auth_valid_until = datetime.now(timezone.utc)
            self.token = None
        else:
            self.auth = True
            self.auth_client = Client(auth_wsdl, transport=Transport(session=session),  wsse=UsernameToken(username, password=password))
            self.auth_valid_until = datetime.now(timezone.utc)
            self.token = None

    def _print_last_message_exchange(self):
        """Prints out last sent and received SOAP messages"""

        messages = {"SENT":     self.history.last_sent,
                    "RECEIVED": self.history.last_received}
        print("-" * 50)

        for message in messages:

            print(f"### {message} HTTP HEADER ###")
            print('\n' * 1)
            print(messages[message]["http_headers"])
            print('\n' * 1)
            print(f"### {message} HTTP ENVELOPE START ###")
            print('\n' * 1)
            print(etree.tostring(messages[message]["envelope"], pretty_print=True).decode())
            print(f"### {message} HTTP ENVELOPE END ###")
            print('\n' * 1)

        print("-" * 50)


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

    def request_security_token(self, pretty_print=False):
        """Return the token as string and it's validity time"""
        token_string = self.auth_client.service.RequestSecurityToken()
        token = etree.fromstring(token_string)
        valid_unitl = aniso8601.parse_datetime(token.find(".//{*}Conditions").attrib['NotOnOrAfter'])

        if pretty_print or self.debug:
            print(json.dumps(xmltodict.parse(token_string), indent=4))

        return token, valid_unitl

    def check_token(self):
        """Check if token is due to expire and renew if needed"""
        utc_now = datetime.now(timezone.utc)

        if utc_now > self.auth_valid_until - aniso8601.parse_duration("PT5S"):
            self.token, self.auth_valid_until = self.request_security_token()
            if self.debug:
                print("Requesting new Auth Token")

        elif self.debug:
            print(f"Auth Token still valid for {self.auth_valid_until - utc_now}")

    def create_saml_header(self):
        """Create SOAP SAML authentication header element for zeep"""
        self.check_token()
        WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
        return [ElementMaker(namespace=WSSE).Security(self.token)]

    def execute_operation(self, operation_xml):
        """ExecuteOperation(payload: xsd:base64Binary) -> return: ns0:resultDto"""
        response = self.client.service.ExecuteOperation(operation_xml, _soapheaders=self.create_saml_header())
        return response

    def publication_request(self, content_type, file_path_or_file_object):
        """PublicationRequest(dataset: ns0:opdeFileDto) -> return: ns0:resultDto,
        ns0:opdeFileDto(id: xsd:string, type: xsd:string, content: xsd:base64Binary)"""

        if type(file_path_or_file_object) == str:

            with open(file_path_or_file_object, "rb") as file_object:
                file_string = file_object.read()

            file_name = os.path.basename(file_path_or_file_object)

        else:
            file_string = file_path_or_file_object.getvalue()
            file_name = file_path_or_file_object.name

        payload = {"id": file_name, "type": content_type, "content": file_string}

        response = self.client.service.PublicationRequest(payload, _soapheaders=self.create_saml_header())

        return response

    def query_object(self, object_type="IGM", metadata_dict = "", components = [], dependencies = []):
        """
        objec_type ->IGM, CGM, BDS
        metadata_dict_example = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00+01:00', 'pmd:timeHorizon': '1D'}
        components_example = [{"opde:Component":"45955-94458-854789358-8557895"}, {"opde:Component":"45955-94458-854789358-8557895"}]
        dependencies_example = [{"opde:DependsOn":"45955-94458-854789358-8557895"}, {"opde:Supersedes":"45955-94458-854789358-8557895"}, {"opde:Replaces":"45955-94458-854789358-8557895"}] """

        query_id = "pyquery_{api_version}_{uuid}".format(uuid=uuid.uuid4(), api_version=self.API_VERSION)

        _QueryObject = self.operations.QueryObject.format(query_id=query_id, object_type=object_type).encode()

        if metadata_dict != "":
            _QueryObject = add_xml_elements(_QueryObject, ".//opdm:OPDMObject", metadata_dict)

        for component in components:
            _QueryObject = add_xml_elements(_QueryObject, ".//opde:Components", component)

        for dependency in dependencies:
            _QueryObject = add_xml_elements(_QueryObject, ".//opde:Dependencies", dependency)

        #print(_QueryObject.decode())

        result = xmltodict.parse(etree.tostring(self.execute_operation(_QueryObject)), xml_attribs=False)

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

        result = xmltodict.parse(etree.tostring(self.execute_operation(new_GetContentResult.encode())), xml_attribs=False)

        try:
            print("File downloded")
            print(result['sm:GetContentResult']['sm:part']['opdm:Profile']['opde:Content']) # Print url of the

        except:
            print("Error oqqoured")

        return result

    def publication_list(self):

        result = self.execute_operation(self.operations.PublicationsList.encode())
        return result

    def publication_subscribe(self, subscription_id=str(uuid.uuid4()), publication_id="ENTSOE-OPDM-Publish-CGM", mode="DIRECT_CONTENT", object_type="CGM", metadata_dict={}):
        """
        Set up subscription for data models. By default sets up subscription for CGM

        publication_id -> request for available with publication_list()
        mode -> META?, DIRECT_CONTENT, FULL? # TODO check the ? options
        objec_type -> IGM, CGM, BDS
        metadata_dict_example = {'pmd:cgmesProfile': 'SV', 'pmd:scenarioDate': '2018-12-07T00:30:00+01:00', 'pmd:timeHorizon': '1D'}
        """

        PublicationSubscribe = f"""<sm:PublicationSubscribe xmlns="http://entsoe.eu/opde/ServiceModel/1/0"
                                    xmlns:sm="http://entsoe.eu/opde/ServiceModel/1/0"
                                    xmlns:opde="http://entsoe.eu/opde/ObjectModel/1/0"
                                    xmlns:pmd="http://entsoe.eu/opdm/ProfileMetaData/1/0"
                                    xmlns:opdm="http://entsoe.eu/opdm/ObjectModel/1/0">
                                    <sm:part name="subscriptionID">{subscription_id}</sm:part>
                                    <sm:part name="publicationID">{publication_id}</sm:part>
                                    <sm:part name="mode">{mode}</sm:part>
                                    <sm:part name="pattern" type="opde:MetaDataPattern">
                                        <opdm:OPDMObject>
                                            <pmd:Object-Type>{object_type}</pmd:Object-Type>
                                        </opdm:OPDMObject>
                                        </sm:part>
                                    </sm:PublicationSubscribe>""".encode()

        if metadata_dict != "":
            PublicationSubscribe = add_xml_elements(PublicationSubscribe, ".//opdm:OPDMObject", metadata_dict)

        return xmltodict.parse(etree.tostring(self.execute_operation(PublicationSubscribe)), xml_attribs=False)

    def publication_cancel_subscription(self, subscription_id):
        """Cancel subscription by subscription ID"""

        new_PublicationSubscriptionCancel = self.operations.PublicationSubscriptionCancel.format(subscription_id)
        result = self.execute_operation(new_PublicationSubscriptionCancel)

        return result




# DEBUG
if __name__ == '__main__':


    server = 'https://test-ba-opde.elering.sise:8443'

    service = OPDMservice(server, username="user", password="pass", debug=True)


    # Query model part example

##    # Available profile meta
##    """
   # "pmd:content-reference": "CGMES/1D/ELERING/20190712/93000/SV/20190712T0930Z_1D_ELERING_SV_001.zip",
   # "pmd:conversationId": "-581868906",
   # "pmd:fileName": "20190712T0930Z_1D_ELERING_SV_001.zip",
   # "pmd:isFullModel": "true",
   # "pmd:TSO": "ELERING",
   # "pmd:modelingAuthoritySet": "http://www.elering.ee/OperationalPlanning",
   # "pmd:timeHorizon": "1D",
   # "pmd:contentType": "CGMES",
   # "pmd:modelProfile": "http://entsoe.eu/CIM/StateVariables/4/1",
   # "pmd:validFrom": "20190712T0930Z",
   # "pmd:modelid": "3c09a995-d250-460d-9b34-09f75fc2cade",
   # "pmd:creationDate": "2019-07-11T18:16:46Z",
   # "pmd:cgmesProfile": "SV",
   # "pmd:version": "001",
   # "pmd:fullModel_ID": "3c09a995-d250-460d-9b34-09f75fc2cade",
   # "pmd:modelPartReference": "ELERING",
   # "pmd:description": "ELERING AP--Base-Network",
   # "pmd:profileSize": "1282790",
   # "pmd:scenarioDate": "2019-07-12T09:30:00Z",
   # "pmd:versionNumber": "001"
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



    # Query model example

    # query_id, response = service.query_object(object_type = "IGM", metadata_dict = {'pmd:scenarioDate': '2019-07-28T00:30:00', 'pmd:timeHorizon': '1D'})
    #
    # list_of_responses = []
    #
    # for single_response in response['sm:QueryResult']['sm:part'][1:]:
    #     list_of_responses.append(single_response['opdm:OPDMObject'])
    #
    # # Create nice table view
    # import pandas
    # pandas.set_option("display.max_rows", 12)
    # pandas.set_option("display.max_columns", 10)
    # pandas.set_option("display.width", 1500)
    # #pandas.set_option('display.max_colwidth', -1)
    #
    # data = pandas.DataFrame(list_of_responses)


    # Get content example

##    model_or_modelpart_UUID = "3c09a995-d250-460d-9b34-09f75fc2cade"
##    response = service.get_content(model_or_modelpart_UUID)
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
