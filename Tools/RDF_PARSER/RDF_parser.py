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
pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)
#pandas.set_option('display.max_colwidth', -1)

# FUNCTIONS - go down for sample code

def print_duration(text, start_time):

    """Print duration between now and start time
    Input: text, start_time
    Output: duration (in seconds), end_time"""

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(text, duration)

    return duration, end_time

def load_RDF_objects_from_XML(path_or_fileobject):

    # START TIMER
    start_time = datetime.datetime.now()

    # LOAD XML
    parser =  etree.XMLParser(remove_comments=True, collect_ids = False)
    parsed_xml = etree.parse(path_or_fileobject, parser = parser)
    model_id = parsed_xml.find("./").attrib.values()[0].replace("urn:uuid:", "") # Lets asume that the first RDF element describes the whole document
    #model_id = parsed_xml.find(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}FullModel").attrib.values()[0].replace("urn:uuid:", "")
    _,start_time = print_duration("XML loaded to tree object", start_time)


    # EXTRACT RDF OBJECTS
    RDF_objects = parsed_xml.getroot().iterchildren()
    _,start_time = print_duration("All children put to a generator", start_time)



    return RDF_objects, model_id


def load_RDF_to_dataframe(path_or_fileobject):

    RDF_objects, INSTANCE_ID = load_RDF_objects_from_XML(path_or_fileobject)

    start_time = datetime.datetime.now()

    data_list = []

    #lets create all variables, so that in loops they are reused, rather than new ones are created, green thinking
    ID      = ""
    KEY     = ""
    VALUE   = ""


    # TODO - a lot of replacements have been done using replace function, but is it valid that these charecaters are not present in UUID-s?

    for object in RDF_objects:

        ID = object.attrib.values()[0].replace("urn:uuid:", "").replace("#_", "").replace("_", "")
        #ID_TYPE = object.attrib.keys()[0].split("}")[1] # Adds column to identifi "ID" and "about" types of ID
        #KEY = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Type' # If we would like to keep all with correct namespace
        KEY = 'Type'
        VALUE = object.tag.split("}")[1]

        #data_list.append([ID, ID_TYPE, KEY, VALUE]) # If using ID TYPE
        data_list.append([ID, KEY, VALUE, INSTANCE_ID])

        for element in object.iterchildren():

            KEY = element.tag.split("}")[1]
            VALUE = element.text

            if VALUE == None:

                VALUE = element.attrib.values()[0].replace("urn:uuid:", "").replace("#_", "")

            #data_list.append([ID, ID_TYPE, KEY, VALUE]) # If using ID TYPE
            data_list.append([ID, KEY, VALUE, INSTANCE_ID])

    _,start_time = print_duration("All values put to data list", start_time)


    data = pandas.DataFrame(data_list, columns = ["ID", "KEY", "VALUE", "INSTANCE_ID"])
    _,start_time = print_duration("Data list loaded to DataFrame", start_time)


    return data

def find_all_xmls(list_of_paths_to_zip_globalzip_xml):
    """Retunrs list of file objects and/or paths"""

    xml_files_list = []
    zip_files_list = []

    for item in list_of_paths_to_zip_globalzip_xml:

        if ".xml" in item or ".rdf" in item:
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

            if ".xml" in zipped_file or ".rdf" in zipped_file:
                file_object = BytesIO(zip_container.read(zipped_file))
                file_object.name = zipped_file
                xml_files_list.append(file_object)
                print("Added: {}".format(zipped_file))

            elif ".zip" in zipped_file:
                zip_files_list.append(BytesIO(zip_container.read(zipped_file)))
                print("Added for further processing: {}".format(zipped_file))

            else: print("Not supported file: {}".format(zipped_file))


    return xml_files_list

def load_all_to_dataframe(list_of_paths_to_zip_globalzip_xml):
    list_of_xmls = find_all_xmls(list_of_paths_to_zip_globalzip_xml)

    data = pandas.DataFrame()

    for xml in list_of_xmls:
        file_name = xml

        if type(xml) != str:
            file_name = xml.name

        print("Loading {}".format(file_name))

        data = data.append(load_RDF_to_dataframe(xml), ignore_index = True)

    return data


def type_tableview(data, type_name):

    "Creates a table view of all elements of defined type, with their parameters in columns"

    type_id_list = data.query("VALUE == '{}' & KEY == 'Type'".format(type_name))["ID"].tolist()
    type_data = data[data.ID.isin(type_id_list)].drop_duplicates(["ID", "KEY"]) # There can't be duplicate ID and KEY pairs for pivot, but this will lose data on full model DependantOn and other info, solution would be to use pivot table function.

    data_view = type_data.pivot(index="ID", columns = "KEY")["VALUE"]

    return data_view

pandas.DataFrame.type_tableview = type_tableview #Lets extend this fuctionality to pandas DataFrame


def reference_tableview(data, reference):

    "Creates a table view of all elements that refer to specific element, returns only id, type, name"

    reference_list = data.query("VALUE == '{}'".format(reference))["ID"].tolist()
    reference_data = data[data.ID.isin(reference_list)].drop_duplicates(["ID", "KEY"]) # There can't be duplicate ID and KEY pairs for pivot

    data_view = reference_data.pivot(index="ID", columns="KEY")["VALUE"][["Type", "IdentifiedObject.name"]]

    return data_view

pandas.DataFrame.reference_tabeleview = reference_tableview #Lets extend this fuctionality to pandas DataFrame


def types_dict(data):

    "Returns dictionary with all types as keys and number of their occurrences as values"

    types_dictionary = data[(data.KEY == "Type")]["VALUE"].value_counts().to_dict()

    return  types_dictionary

pandas.DataFrame.types_dict = types_dict


# END OF FUNCTIONS


# TEST and examples
if __name__ == '__main__':


    path = "FlowExample.zip"

    #path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

    data = load_all_to_dataframe([path])

    print("Loaded types")
    print(data[(data.KEY == "Type")]["VALUE"].value_counts())

    print(data.type_tableview("ACLineSegment"))


    # model = "FlowExample.zip"
    #
    # rdfs = "C:\Users\kristjan.vilgo\Downloads\ENTSOE_CGMES_v2.4.15_04Jul2016_RDFS\EquipmentProfileCoreOperationRDFSAugmented-v2_4_15-4Jul2016.rdf"
    #
    # data = load_all_to_dataframe([model, rdfs])
    #
    #
    # values_in_linesegment = data.query("VALUE == '#ACLineSegment'")
    # values_in_powertransform_end = data.query("VALUE == '#PowerTransformerEnd'")
    # data.query("ID == '#PowerTransformerEnd.r'")
    # data.query("ID == '#Resistance'")
    #
    # data_types = data.query("KEY == 'dataType'")["VALUE"].drop_duplicates()




# for quick export of data use data[data.VALUE == "PowerTransformer"].to_csv(export.csv) or data[data.VALUE == "PowerTransformer"].to_clipboard() and  paste to excel, for other method refer to pandas manual


