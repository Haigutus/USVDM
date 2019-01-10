#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     13.12.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from __future__ import print_function

from lxml import etree
import pandas
import datetime

#pandas.set_option("display.height", 1000)
pandas.set_option("display.max_rows", 10)
pandas.set_option("display.max_columns", 4)
pandas.set_option("display.width", 1000)

start_time = datetime.datetime.now()
pervious_timestamp = start_time

parsed_xml = etree.parse(r"C:\Users\kristjan.vilgo\Desktop\IGM_hour23\IGM_hour23\20180310T2330Z_2D_ELERING_TP_001.xml")
#parsed_xml = etree.parse(r"C:\Users\kristjan.vilgo\Downloads\20180829T0030Z_NG_EQ_001.xml")

time_now = datetime.datetime.now()
print("XML loaded to tree object", (time_now - pervious_timestamp).total_seconds())
pervious_timestamp = time_now


RDF_objects = parsed_xml.getroot().iterchildren()

time_now = datetime.datetime.now()
print("All children put to a generator", (time_now - pervious_timestamp).total_seconds())
pervious_timestamp = time_now



data_list = []

for object in RDF_objects:

    ID = object.attrib.values()[0]
    ID_TYPE = object.attrib.keys()[0]
    KEY = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Type'
    VALUE = object.tag

    data_list.append([ID, ID_TYPE, KEY, VALUE])

    for element in object.iterchildren():

        KEY = element.tag
        VALUE = element.text

        data_list.append([ID, ID_TYPE, KEY, VALUE])

        #data = data.append(pandas.DataFrame([{"ID": ID, "ID_TYPE": ID_TYPE, "KEY": KEY, "VALUE": VALUE}]))

data = pandas.DataFrame(data_list, columns = ["ID", "ID_TYPE", "KEY", "VALUE"])

time_now = datetime.datetime.now()
print("Loaded to dataframe", (time_now - pervious_timestamp).total_seconds())
pervious_timestamp = time_now
