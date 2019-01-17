#-------------------------------------------------------------------------------
# Name:        RDF parser
# Purpose:     Loads RDF XMLs from zip and xml files to pandas DataFrame in a triplestore manner
#
# Author:      kristjan.vilgo
#
# Created:     13.12.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     GPLv2
#-------------------------------------------------------------------------------
from __future__ import print_function

from io import BytesIO

from lxml import etree
import pandas
import datetime
import zipfile

#pandas.set_option("display.height", 1000)
pandas.set_option("display.max_rows", 30)
pandas.set_option("display.max_columns", 4)
pandas.set_option("display.width", 1000)

# FUNCTIONS - go down for sample code

def load_RDF_objects_from_XML(path_or_fileobject):

    # START TIMER
    start_time = datetime.datetime.now()

    # LOAD XML
    parsed_xml = etree.parse(path_or_fileobject)
    model_id = parsed_xml.find(".//{*}FullModel").attrib.values()[0].replace("urn:uuid:", "")

    # PRINT DURATION
    end_time = datetime.datetime.now()
    print("XML loaded to tree object", (end_time - start_time).total_seconds())


    # EXTRACT RDF OBJECTS
    start_time = end_time
    RDF_objects = parsed_xml.getroot().iterchildren()
    end_time = datetime.datetime.now()

    print("All children put to a generator", (end_time - start_time).total_seconds())

    return RDF_objects, model_id


def load_RDF_to_dataframe(path_or_fileobject):

    RDF_objects, PROFILE_UUID = load_RDF_objects_from_XML(path_or_fileobject)

    start_time = datetime.datetime.now()

    data_list = []


    # TODO - a lot of replacemtns have been done using replace function, but is it valid that these charecaters are not present in UUID-s?

    for object in RDF_objects:

        ID = object.attrib.values()[0].replace("urn:uuid:", "").replace("#_", "").replace("_", "")
        #ID_TYPE = object.attrib.keys()[0].split("}")[1] # Adds column to identifi "ID" and "about" types of ID
        #KEY = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Type' # If we would like to keep all with correct namespace
        KEY = 'Type'
        VALUE = object.tag.split("}")[1]

        #data_list.append([ID, ID_TYPE, KEY, VALUE]) # If using ID TYPE
        data_list.append([ID, KEY, VALUE, PROFILE_UUID])

        for element in object.iterchildren():

            KEY = element.tag.split("}")[1]
            VALUE = element.text

            if VALUE == None:
                VALUE = element.attrib.values()[0].replace("urn:uuid:", "").replace("#_", "")

            #data_list.append([ID, ID_TYPE, KEY, VALUE]) # If using ID TYPE
            data_list.append([ID, KEY, VALUE, PROFILE_UUID])


    data = pandas.DataFrame(data_list, columns = ["ID", "KEY", "VALUE", "PROFILE_UUID"])

    end_time = datetime.datetime.now()
    print("Loaded to dataframe", (end_time - start_time).total_seconds())

    return data

def find_all_xmls(list_of_paths_to_zip_globalzip_xml):
    """Retunrs list of file objects and/or paths"""

    xml_files_list = []
    zip_files_list = []

    for item in list_of_paths_to_zip_globalzip_xml:

        if ".xml" in item:
            xml_files_list.append(item)
            print("Added: {}".format(item))

        elif ".zip" in item:
            zip_files_list.append(item)
            print("Added for further processing: {}".format(item))

        else: print("Not supported file: {}".format(item))


    for zip_file_path in zip_files_list:

        zip_container = zipfile.ZipFile(zip_file_path)
        zipped_files  = zip_container.namelist()

        for zipped_file in zipped_files:

            if ".xml" in zipped_file:
                xml_files_list.append(BytesIO(zip_container.read(zipped_file)))
                print("Added: {}".format(zipped_file))

            elif ".zip" in zipped_file:
                zip_files_list.append(BytesIO(zip_container.read(zipped_file)))
                print("Added for further processing: {}".format(zipped_file))

            else: print("Not supported file: {}".format(zipped_file))


    return xml_files_list

def load_all_to_dataframe(list_of_paths_to_zip_globalzip_xml):
    list_of_xmls = find_all_xmls([path])

    data = pandas.DataFrame()


    for xml in list_of_xmls:
        data = data.append(load_RDF_to_dataframe(xml), ignore_index = True)

    return data


# END OF FUNCTIONS


# TEST and examples
if __name__ == '__main__':

    path = "FlowExample.zip"



    data = load_all_to_dataframe([path])

    print(data)


    print("Loaded model UUID-s")
    model_uuids = data[(data["VALUE"]=="FullModel")]
    print(model_uuids)

    print("Printing loaded profile headers")
    for uuid in list(model_uuids["ID"]):

        print(uuid)

        header = data[(data["ID"]==uuid)]

        print(header[["KEY", "VALUE"]])


    print("Loaded types")
    print(data[(data.KEY == "Type")]["VALUE"].value_counts())

    print("Loaded attributes")
    print(data.KEY.value_counts())


    print("All transformers rated S")
    print(data[data.KEY == "PowerTransformerEnd.ratedS"])


    print("Powertransformers")
    print(data[data.VALUE == "PowerTransformer"])

    print("One winding data")
    print(data[data.ID == "12d773ab-1521-4e09-8a45-88b5eebf6fdd"])

    # for quick export of data use data[data.VALUE == "PowerTransformer"].to_csv(export.csv) or data[data.VALUE == "PowerTransformer"].to_clipboard() and  paste to excel, for other method refer to pandas manual


    #data = load_RDF_to_dataframe(r"C:\Users\kristjan.vilgo\Desktop\IGM_hour23\IGM_hour23\20180310T2330Z_2D_ELERING_TP_001.xml")