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
import pytz
import aniso8601

import zipfile
import io

import time

from uuid import uuid4

from collections import OrderedDict

import pandas
#pandas.set_option('display.height', 1000)
pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.width', 1000)


CET = pytz.timezone("Europe/Brussels")
now = datetime.now(CET)

def get_year_start(date_time = now):

    year_start = date_time.replace(month = 1, day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)

    return year_start


def get_month_start(date_time = now):

    month_start = date_time.replace(day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)

    return month_start


def get_week_start(date_time = now):

    weekday = date_time.weekday()

    day_start = get_day_start(date_time)

    week_start = day_start - datetime.timedelta(days = weekday)

    return week_start


def get_day_start(date_time = now):

    day_start =  date_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

    return day_start


def get_hour_start(date_time = now):

    hour_start =  date_time.replace(minute = 0, second = 0, microsecond = 0)

    return hour_start




def timestamp_range(start_date, end_date, ISO_step):

    timestamp_list = []
    timestamp = start_date

    while timestamp <= end_date:

        timestamp_list.append(timestamp)
        timestamp += aniso8601.parse_duration(ISO_step)

    return timestamp_list


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
        <xs:element name="scenarioDate" type="xs:date"/>
        <xs:element name="scenarioTime" type="xs:time" minOccurs="0" maxOccurs="1"/>
        <xs:element name="version" type="xs:int" minOccurs="0" maxOccurs="1">"""


    # TODO - validate fileds

    # Put metadata to ordered dict to keep correct sequence for XML generation
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

    # Put metadata to ordered dict to keep correct sequence for XML generation
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
    return zipfile.ZipFile(io.BytesIO(message['receivedMessage']['content']))

def save_zip_message(message, path):
    "Saves ZIP message to path"

    zip_file = parse_zip_attachment(message)
    zip_file.write(path)
    zip_file.close()


def parse_QAReport(xml_string):
    "Parse relevant infromation form QAReport"

    xml = etree.fromstring(xml_string)

    QAReport_element = xml.find(".//{*}QAReport")

    if QAReport_element is None:
        QAReport_element = xml

    meta = {'QAReport_' + k: v for k, v in QAReport_element.attrib.items()}
    meta["opdm_version"] = xml.get("opdm-version", "")

    if xml.find(".//{*}Id") is not None:
        meta["opde_id"] = xml.find(".//{*}Id").text

    if xml.find(".//{*}processible") is not None:
        meta["processible"] = xml.find(".//{*}processible").text


    for report in QAReport_element.getchildren():
        report_meta = report.attrib
        report_meta["type"] = report.tag.split("}")[1]

        current_meta = meta.copy()
        current_meta.update(report_meta)


        # Get violations
        violations = []
        violations_dict = []
        for violation_element in report.findall("{*}RuleViolation"):

            # Extract violation data
            viloation = dict(violation_element.attrib)
            message   = str(violation_element.find("{*}Message").text)

            # Add to violoations list
            violations.append((viloation["ruleId"], viloation["validationLevel"], viloation["severity"], message))

            # Make dict
            viloation["message"]=message
            violations_dict.append(viloation)

    # Add viloations to meta
    current_meta["violations"]      = pandas.DataFrame(violations, columns = ["ruleId", "validationLevel", "severity", "message"])

    current_meta["WARNINGS"]        = str(current_meta["violations"].query("severity == 'WARNING'")["severity"].count())
    current_meta["WARNINGS_INFO"]   = current_meta["violations"].query("severity == 'WARNING'")["ruleId"].value_counts().to_dict()
    current_meta["ERRORS"]          = int(current_meta["violations"].query("severity == 'ERROR'")["severity"].count())
    current_meta["ERRORS_INFO"]     = current_meta["violations"].query("severity == 'ERROR'")["ruleId"].value_counts().to_dict()
    current_meta["MAX_ERROR_LEVEL"] = str(current_meta["violations"].query("severity == 'ERROR'")["validationLevel"].fillna(0).max())

    current_meta["violations"]      = violations_dict



    return current_meta#.drop(columns=["violations"]).to_csv("C:\Users\kristjan.vilgo\Downloads\example_data.csv")




# Enumerations defined for messages

tso_list = ['50Hertz', 'Amprion', 'APG', 'CEPS', 'CGES', 'ELES', 'ELIA', 'EMS',
'Energinet.DK West', 'ESO', 'HOPS', 'IPTO', 'MAVIR', 'MEPSO', 'NOSBiH', 'OST',
'PSE', 'REE', 'REN', 'RTE', 'SEPS', 'Swissgrid', 'TEIAS', 'TenneT Neth.',
'TenneT. Ger', 'Terna', 'Transelectrica', 'TransnetBW', 'Creos',
'Energinet.DK East', 'Fingrid', 'Statnett', 'Svenska Kraftnät',
'AST', 'Elering', 'Litgrid', 'National Grid', 'Eirgrid', 'UKRENERGO'] #'Eirgrid/SONI'

RSCname_list  = ['balticrsc', 'coreso', 'nordicrsc', 'sccrsci', 'tscnet']

CGMType_list  = ['ba', 'ce', 'eu', 'in', 'no', 'uk']


def parse_error_message(message):
    "Extract error message"
    error_message = etree.fromstring(message['receivedMessage']['content']).find(".{*}message").text

    return error_message


def remove_message():
    "Removes message from que"
    message = service.receive_message("ENTSOE-QAS-QueryResult", False)
    service.confirm_received_message(message['receivedMessage']['messageID'])
    print(message['remainingMessagesCount'])





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
##    <q:tso>ELERING</q:tso>
##    <q:scenarioDate>2019-06-25</q:scenarioDate>
##    <!--Optional:-->
##    <q:scenarioTime>00:30:00</q:scenarioTime> <!-- if defined, only one timestamp will be returned -->
##    <!--<q:version>3</q:version> -->          <!-- if not defined, latest version will be returned -->
##  </q:IGM>
##</q:QASQuery>
##"""

