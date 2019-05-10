#-------------------------------------------------------------------------------
# Name:        Generate QAR message
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     05.03.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, os
sys.path.append(r'C:\USVDM\Tools\MADES_API')
import OPDM_SOAP_client as OPDM_API
import EDX_MADES_client as EDX_API

from XML_CONF_from_XSD import *
from lxml.builder import ElementMaker

from datetime import datetime
import aniso8601
import pytz

import ftplib
import pandas



CET = pytz.timezone("Europe/Brussels")
now = datetime.now(CET)
meta_separator = "_"

elements_dictionary, complex_variables_dictionary, variables_dictionary = create_conf_from_XSD("C:\USVDM\Tools\XML_GENERATOR\QAR_v2_20170113\QAR_v2_20170113.xsd")

def complex_variable_name(name_string, position = "0"):
    """To catch case where name is written wrong"""

    name = complex_variables_dictionary[name_string][str(position)]["DATA"]["element"]

    return name


def get_day_start(date_time = now):

    day_start =  date_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

    return day_start


def metadata_from_filename(file_name):

    print(file_name)
    file_metadata = {}
    file_name, file_metadata["file_type"] = file_name.split(".")


    if "_EQ_" in file_name or "_BD_" in file_name:

        file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)
        file_metadata["process_type"] = ""

    else:

        try:
            file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)

        except:
            print ("Non CGMES file {}".format(file_name))

    return file_metadata


def profile_query_result_to_dataframe(query_result):

    if query_result.get("sm:OperationFailure", False) != False:

        print("Query failure: ")

        query_status = response["sm:OperationFailure"]["sm:part"]["opde:Error"]['opde:technical-details']['opde:technical-detail']

        print(query_status)

        return

    if type(query_result['sm:QueryResult']['sm:part']) == str:

        print("No data")

        return

    query_result['sm:QueryResult']['sm:part'].pop(0)

    query_dataframe = pandas.DataFrame(query_result['sm:QueryResult']['sm:part'])

    return query_dataframe


server_ip   = '185.7.252.111'
username    = 'Elering_baltic-rsc.eu'
password    = 'Gb8JCNF'

TSOs = ['ELERING', 'LITGRID', 'AST']





delivery_date = get_day_start() + aniso8601.parse_duration("P0D")
base_bath = "/RSC/CGM/OUT/{}/".format(delivery_date.strftime("%Y%m%d"))


session = ftplib.FTP(server_ip, username, password)
session.cwd(base_bath)
files_list = session.nlst()

meta_list = []

for n, file_name in enumerate(files_list):

    print(file_name)

    if ".zip" in file_name:

        meta = metadata_from_filename(file_name)
        meta["file_path"] = os.path.join(base_bath, file_name)
        meta_list.append(meta)

    else:
        print("Unsupported file {}".format(file_name))

cgm_profiles = pandas.DataFrame(meta_list)

timestamps = cgm_profiles["date_time"].unique()

timestamp = cgm_profiles["date_time"].unique()[0]
TSO = TSOs[0]
instance_type = "SV"


query_id, query_result = API.query_object(object_type = "IGM", metadata_dict = {'pmd:TSO': TSO, 'pmd:validFrom': timestamp})

try:
    profile_list = query_result['sm:QueryResult']['sm:part'][1]['opdm:OPDMObject']["opde:Component"]
except:
    print("No profiles returned")
    continue

#cgm_profiles.query("date_time == '{date_time}' & model_authority == '{model_authority}' & profile == 'SV'".format(date_time = timestamp, model_authority = TSO))

##E = ElementMaker(namespace="http://entsoe.eu/checks", nsmap={None:'http://entsoe.eu/checks'})
##
##QAReport_attributes = {  'created': datetime.utcnow().isoformat(sep='T'),#", timespec='seconds'),
##                         'schemeVersion': "2.0",
##                         'serviceProvider': "Baltic"}
##
##QAReport = E(complex_variable_name("QAReport"), "", QAReport_attributes)
##
##IGM_attributes = {   'created': created,
##                     'processType': processType,
##                     'qualityIndicator': 'Plausible',
##                     'scenarioTime': scenarioTime,
##                     'tso': tso,
##                     'version': version}
##
##
##IGM = E(complex_variable_name("IGM"),"",IGM_attributes)
##QAReport.append(IGM)
##
##resource = E(complex_variable_name("IGM","1"), "UUID")
##IGM.append(resource)
##
##
##
##print etree.tostring(QAReport, pretty_print=True, xml_declaration=True, encoding='UTF-8')
##
##
####[{'value': 'Diagnostics'},
####{'value': 'Invalid - dangling references'},
####{'value': 'Invalid - inconsistent data'},
####{'value': 'Invalid - preconditions PF'},
####{'value': 'Plausible'},
####{'value': 'Processible'},
####{'value': 'Rejected - File cannot be parsed'},
####{'value': 'Rejected - Invalid CGMES file'},
####{'value': 'Rejected - Invalid file name'},
####{'value': 'Rejected - Invalid file type'},
####{'value': 'Rejected - OCL rule violation(s)'},
####{'value': 'Substituted'},
####{'value': 'Unavailable'},
####{'value': 'Unlikely'},
####{'value': 'Valid'},
####{'value': 'Warning - non fatal inconsistencies'}]