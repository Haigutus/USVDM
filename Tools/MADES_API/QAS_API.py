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

server = "https://test-ba-opde.elering.sise"

# Neede only if basic auth is set up for UI
username = "admin"  #raw_input("UserName")
password = "sadmin" #raw_input("PassWord")


now       = datetime.now()
namespace = "http://entsoe.eu/checks"
root_name = "QASQuery"
scheme_ver= "1"

E = ElementMaker(namespace=namespace, nsmap={None:namespace})
root = E(root_name, schemeVersion=scheme_ver, created=now.isoformat())

CGM = E("CGM")

##<xs:element name="processType" type="entso-e:ProcessType"/>
##<xs:element name="RSCName" type="entso-e:RSCName"/>
##<xs:element name="CGMType" type="entso-e:CGMType"/>
##<xs:element name="scenarioDate" type="xs:date"/>
##<xs:element name="scenarioTime" type="xs:time" minOccurs="0" maxOccurs="1"/>
##<xs:element name="version" type="xs:int" minOccurs="0" maxOccurs="1">

CGM_meta_dict = dict(   processType="1D",
                        RSCName="TSCNET",
                        CGMType="BA",
                        scenarioDate="2019-06-12",
                        scenarioTime="03:30:00")

for key in CGM_meta_dict.keys():
    CGM.append(E(key, CGM_meta_dict[key]))

root.append(CGM)

print(etree.tostring(root, pretty_print = True))


CGM_example_query = """
<q:QASQuery created="2008-09-29T03:49:45" schemeVersion="1" xmlns:q="http://entsoe.eu/checks">
  <q:CGM>
    <q:processType>1D</q:processType>
    <q:RSCName>TSCNET</q:RSCName>
    <q:CGMType>CE</q:CGMType>
    <q:scenarioDate>2019-06-12</q:scenarioDate>
    <!--Optional:-->
    <!--<q:scenarioTime>03:30:00</q:scenarioTime> --> <!-- if defined, only one timestamp will be returned -->
    <!--<q:version>0</q:version -->                   <!-- if not defined, latest version will be returned -->
  </q:CGM>
</q:QASQuery>
"""

IGM_example_query = """
<q:QASQuery created="2008-09-29T03:49:45" schemeVersion="1" xmlns:q="http://entsoe.eu/checks">
  <q:IGM>
    <q:processType>1D</q:processType>
    <q:tso>RTE</q:tso>
    <q:scenarioDate>2019-06-25</q:scenarioDate>
    <!--Optional:-->
    <q:scenarioTime>00:30:00</q:scenarioTime> <!-- if defined, only one timestamp will be returned -->
    <!--<q:version>3</q:version> -->                  <!-- if not defined, latest version will be returned -->
  </q:IGM>
</q:QASQuery>
"""

service = create_client(server, username, password, debug = False)

message_ID = service.send_message("SERVICE-QAS", "ENTSOE-QAS-Query", IGM_example_query)


status = service.check_message_status(message_ID)


message = service.receive_message("ENTSOE-QAS-QueryResult")

zip_file = zipfile.ZipFile(StringIO.StringIO(message.attachments[0].content))
zip_file.namelist()

files = [zip_file.read(name) for name in zip_file.namelist()]

meta_list = []

for xml_string in files:
    xml = etree.fromstring(xml_string)



    QAReport_element = xml.find(".//{*}QAReport")

    meta = {'QAReport_' + k: v for k, v in QAReport_element.attrib.items()}
    meta["opdm_version"] = xml.get("opdm-version", "")


    for report in QAReport_element.getchildren():
        report_meta = report.attrib
        report_meta["type"] = report.tag.split("}")[1]

        current_meta = meta.copy()
        current_meta.update(report_meta)

        violations = []
        for violation_element in report.findall("{*}RuleViolation"):

            viloation = violation_element.attrib
            viloation["message"] = violation_element.find("{*}Message").text
            violations.append(viloation)

        current_meta["violations"] = violations

        meta_list.append(current_meta)

import pandas
pandas.DataFrame(meta_list).drop(columns=["violations"]).to_csv("C:\Users\kristjan.vilgo\Downloads\example_data.csv")

##message = service.receive_message("ENTSOE-QAS-QueryResult", False)
##service.confirm_received_message(message['receivedMessage']['messageID'])

for xml_file in zip_file.namelist(): print(xml_file)

