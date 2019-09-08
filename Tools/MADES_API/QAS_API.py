#-------------------------------------------------------------------------------
# Name:        QAS API
# Purpose:     Query validation reports from
#
# Author:      kristjan.vilgo
#
# Created:     23.07.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPL2
#-------------------------------------------------------------------------------

from EDX import create_client
from lxml.builder import ElementMaker
from lxml import etree
from datetime import datetime

import zipfile
import StringIO



from collections import OrderedDict

import pandas
#pandas.set_option('display.height', 1000)
pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.width', 1000)


def create_message(query_type, meta):

    now       = datetime.now()
    namespace = "http://entsoe.eu/checks"
    root_name = "QASQuery"
    scheme_ver= "1"

    E       = ElementMaker(namespace=namespace, nsmap={None:namespace})
    root    = E(root_name, schemeVersion=scheme_ver, created=now.isoformat())
    query   = E(query_type)

    for key in meta.keys():

        value = meta[key]

        if value != "":
            query.append(E(key, value))

    root.append(query)

    #print(etree.tostring(root, pretty_print = True))
    return etree.tostring(root, pretty_print = True)


def IGM_query_message(processType, tso, scenarioDate, scenarioTime="", version=""):

    """ <xs:element name="processType" type="entso-e:ProcessType"/>
        <xs:element name="tso" type="entso-e:tso"/>
        <xs:element name="CGMType" type="entso-e:CGMType"/>
        <xs:element name="scenarioDate" type="xs:date"/>
        <xs:element name="scenarioTime" type="xs:time" minOccurs="0" maxOccurs="1"/>
        <xs:element name="version" type="xs:int" minOccurs="0" maxOccurs="1">"""


    # TODO - validate fileds

    meta_dict = OrderedDict()
    meta_dict["processType"]     = processType
    meta_dict["tso"]             = tso
    meta_dict["scenarioDate"]    = scenarioDate
    meta_dict["scenarioTime"]    = scenarioTime
    meta_dict["version"]         = version

    return create_message("IGM", meta_dict)


def CGM_query_message(processType, RSCName, CGMType, scenarioDate, scenarioTime="", version=""):

    """ <xs:element name="processType" type="entso-e:ProcessType"/>
        <xs:element name="RSCName" type="entso-e:RSCName"/>
        <xs:element name="CGMType" type="entso-e:CGMType"/>
        <xs:element name="scenarioDate" type="xs:date"/>
        <xs:element name="scenarioTime" type="xs:time" minOccurs="0" maxOccurs="1"/>
        <xs:element name="version" type="xs:int" minOccurs="0" maxOccurs="1">"""

    # TODO - validate fileds

    meta_dict = OrderedDict()
    meta_dict["processType"]     = processType
    meta_dict["RSCName"]         = RSCName
    meta_dict["CGMType"]         = CGMType
    meta_dict["scenarioDate"]    = scenarioDate
    meta_dict["scenarioTime"]    = scenarioTime
    meta_dict["version"]         = version

    return create_message("CGM", meta_dict)

def parse_zip_attachment(message):
    "Parses base64 mime attachment to zip instance"
    return zipfile.ZipFile(StringIO.StringIO(message.attachments[0].content))

def save_zip_message(message, path):
    "Saves ZIP message to path"

    zip_file = parse_zip_attachment(message)
    zip_file.write(path)
    zip_file.close()


def parse_QAReport(xml_string):
    "Parse relevant infromation form QAReport"

    xml = etree.fromstring(xml_string)

    QAReport_element = xml.find(".//{*}QAReport")

    meta = {'QAReport_' + k: v for k, v in QAReport_element.attrib.items()}
    meta["opdm_version"] = xml.get("opdm-version", "")


    for report in QAReport_element.getchildren():
        report_meta = report.attrib
        report_meta["type"] = report.tag.split("}")[1]

        current_meta = meta.copy()
        current_meta.update(report_meta)


        # Get violations
        violations = []
        for violation_element in report.findall("{*}RuleViolation"):

            # Extract violation data
            viloation = violation_element.attrib
            message   = violation_element.find("{*}Message").text

            # Add to violoations list
            violations.append((viloation["ruleId"], viloation["validationLevel"], viloation["severity"], message))

    # Add viloations to meta
    current_meta["violations"]      = pandas.DataFrame(violations, columns = ["ruleId", "validationLevel", "severity", "message"])
    current_meta["WARNINGS"]        = current_meta["violations"].query("severity == 'WARNING'")["severity"].count()
    current_meta["WARNINGS_INFO"]   = current_meta["violations"].query("severity == 'WARNING'")["ruleId"].value_counts().to_dict()
    current_meta["ERRORS"]          = current_meta["violations"].query("severity == 'ERROR'")["severity"].count()
    current_meta["ERRORS_INFO"]     = current_meta["violations"].query("severity == 'ERROR'")["ruleId"].value_counts().to_dict()
    current_meta["MAX_ERROR_LEVEL"] = current_meta["violations"].query("severity == 'ERROR'")["validationLevel"].max()



    return current_meta#.drop(columns=["violations"]).to_csv("C:\Users\kristjan.vilgo\Downloads\example_data.csv")





tsos=['50Hertz', 'D8', 'Amprion', 'D7', 'APG', 'AT', 'CEPS', 'CZ', 'CGES',\
 'ME', 'ELES', 'SI', 'ELIA', 'BE', 'EMS', 'RS', 'DKW', 'D1', 'ESO', 'BG', \
 'HOPS', 'HR', 'IPTO', 'GR', 'MAVIR', 'HU', 'MEPSO', 'MK', 'NOSBiH', 'BA',\
  'OST', 'AL', 'PSE', 'PL', 'REE', 'ES', 'REN', 'PT', 'RTE', 'FR', 'SEPS',\
   'SK', 'Swissgrid', 'CH', 'TEIAS', 'TR', 'TTN', 'NL', 'D2', 'TTG', 'Terna',\
    'IT', 'Transelectrica', 'RO', 'TransnetBW', 'D4', 'Creos', 'LU', 'DKE',\
     'DK', 'Fingrid', 'FI', 'Statnett', 'NO', 'SE', 'AST', 'LV', 'Elering',\
      'EE', 'Litgrid', 'LT', 'GB', 'NationalGrid', 'NG', 'NGET', 'Eirgrid',\
       'EIRGRIDSONI', 'Ukrenergo', 'WEPS']

areas = ['ba', 'ce', 'eu', 'in', 'no', 'uk']
RSCs  = ['balticrsc', 'coreso', 'nordicrsc', 'sccrsci', 'tscnet']


def parse_error_message(message):
    "Prints error message in response"
    print etree.fromstring(message.attachments[0].content).find(".{*}message").text


def remove_message():
    "Removes message from que"
    message = service.receive_message("ENTSOE-QAS-QueryResult", False)
    service.confirm_received_message(message['receivedMessage']['messageID'])
    print(message['remainingMessagesCount'])


# PROCESS START


server = "https://test-ba-opde.elering.sise"

# Neede only if basic auth is set up for UI
username = "admin"  #raw_input("UserName")
password = "sadmin" #raw_input("PassWord")

service = create_client(server, username, password, debug = False)


TSOs = ["AST", "ELERING", "Litgrid"]

query_counter = 0

##for TSO in TSOs:
##    query_message = IGM_query_message(processType="1D", tso=TSO, scenarioDate="2019-09-01")
##    message_ID = service.send_message("SERVICE-QAS", "ENTSOE-QAS-Query", query_message)
##    print(message_ID)

    ##status = service.check_message_status(message_ID)

##    query_counter += 1


#while query_counter > 0:

message = service.receive_message("ENTSOE-QAS-QueryResult")












error = False
try:
    parse_error_message(message)
    error = True

    print("Removing error message")
    message = service.receive_message("ENTSOE-QAS-QueryResult", False)
    service.confirm_received_message(message['receivedMessage']['messageID'])
    print(message['receivedMessage']['messageID'])

    query_counter -= 1

except:
    pass


if error == False:
    zip_file = parse_zip_attachment(message)
    #print(zip_file.namelist())

    raw_files = [zip_file.read(name) for name in zip_file.namelist()]

    meta_list = []
    for xml_string in raw_files:

        meta_list.append(parse_QAReport(xml_string))

    print(pandas.DataFrame(meta_list).drop(columns=["violations", "ERRORS_INFO", "WARNINGS_INFO"]))

    #pandas.DataFrame(meta_list)#.drop(columns=["violations"]).to_csv("C:\Users\kristjan.vilgo\Downloads\example_data.csv")


##message = service.receive_message("ENTSOE-QAS-QueryResult", False)
##service.confirm_received_message(message['receivedMessage']['messageID'])

##for xml_file in zip_file.namelist(): print(xml_file)



##CGM_example_query = """
##<q:QASQuery created="2008-09-29T03:49:45" schemeVersion="1" xmlns:q="http://entsoe.eu/checks">
##  <q:CGM>
##    <q:processType>1D</q:processType>
##    <q:RSCName>TSCNET</q:RSCName>
##    <q:CGMType>CE</q:CGMType>
##    <q:scenarioDate>2019-06-12</q:scenarioDate>
##    <!--Optional:-->
##    <!--<q:scenarioTime>03:30:00</q:scenarioTime> --> <!-- if defined, only one timestamp will be returned -->
##    <!--<q:version>0</q:version -->                   <!-- if not defined, latest version will be returned -->
##  </q:CGM>
##</q:QASQuery>
##"""
##
##IGM_example_query = """
##<q:QASQuery created="2008-09-29T03:49:45" schemeVersion="1" xmlns:q="http://entsoe.eu/checks">
##  <q:IGM>
##    <q:processType>1D</q:processType>
##    <q:tso>RTE</q:tso>
##    <q:scenarioDate>2019-06-25</q:scenarioDate>
##    <!--Optional:-->
##    <q:scenarioTime>00:30:00</q:scenarioTime> <!-- if defined, only one timestamp will be returned -->
##    <!--<q:version>3</q:version> -->                  <!-- if not defined, latest version will be returned -->
##  </q:IGM>
##</q:QASQuery>
##"""

