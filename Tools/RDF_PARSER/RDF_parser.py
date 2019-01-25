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
pandas.set_option("display.max_columns", 8)
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

    #lets create all variables, so that in loops they are reused, rather than new ones are created, green thinking
    ID      = ""
    KEY     = ""
    VALUE   = ""


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


    end_time = datetime.datetime.now()
    print("All values put to datalist", (end_time - start_time).total_seconds())

    start_time = end_time

    data = pandas.DataFrame(data_list, columns = ["ID", "KEY", "VALUE", "PROFILE_UUID"])

    end_time = datetime.datetime.now()
    print("Data list loaded to DataFrame", (end_time - start_time).total_seconds())




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
        print("Loading {}".format(xml))
        data = data.append(load_RDF_to_dataframe(xml), ignore_index = True)

    return data


def type_view(data, type_name):

    type_id_list = data.query("VALUE == '{}' & KEY == 'Type'".format(type_name))["ID"].tolist()

    type_data = data[data.ID.isin(type_id_list)].drop_duplicates(["ID", "KEY"]) # There can't be duplicate ID and KEY pairs for pivot, but this will lose data on full model DependantOn and other info, solution would be to use pivot table function.

    data_view = type_data.pivot(index="ID", columns = "KEY")["VALUE"]

    return data_view

pandas.DataFrame.type_view = type_view #Lets extend this fuctionality to pandas DataFrame

# END OF FUNCTIONS


# TEST and examples
if __name__ == '__main__':

    path = "FlowExample.zip"

    #path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

    data = load_all_to_dataframe([path])

    print("Loaded types")
    print(data[(data.KEY == "Type")]["VALUE"].value_counts())

    print(data.type_view("SubGeographicalRegion"))

##    print(data)
##
##
##    print("Loaded model UUID-s")
##    model_uuids = data[(data["VALUE"]=="FullModel")]
##    print(model_uuids)
##
##    print("Printing loaded profile headers")
##    for uuid in list(model_uuids["ID"]):
##
##        print(uuid)
##
##        header = data[(data["ID"]==uuid)]
##
##        print(header[["KEY", "VALUE"]])
##
##
##
##    print("Loaded attributes")
##    print(data.KEY.value_counts())
##
##
##    print("All transformers rated S")
##    print(data.query(KEY == "PowerTransformerEnd.ratedS"])
##
##
##    print("Powertransformers")
##    print(data[data.VALUE == "PowerTransformer"]) # Sample of not using query to sort/filter data
##
##    print("One winding data")
##    print(data.query("ID == '12d773ab-1521-4e09-8a45-88b5eebf6fdd'")


##    power_transformers = data.query("VALUE == 'PowerTransformer' & KEY == 'Type'")
##
##    terminals_conducting_equipment = data.query("KEY == 'Terminal.ConductingEquipment'")
##
##    terminals_svpowerflow = data.query("KEY == 'SvPowerFlow.Terminal'")
##    terminals_svvoltage   = data.query("KEY == 'SvVoltage.TopologicalNode'")
##
##    eq_container_terminals = pandas.merge(power_transformers, terminals_conducting_equipment, how = "inner", left_on = 'ID', right_on = 'VALUE', suffixes = ["_eqcontainer", "_terminal"])
##
##    sv_powerflows = pandas.merge(eq_container_terminals, terminals_svpowerflow, how = "inner", left_on = "ID_terminal", right_on = "VALUE", suffixes = ["", "_svpowerflow"])


##KEY                                  IdentifiedObject.name          SubGeographicalRegion.Region                   Type
##ID
##02e3f63a-1100-48fa-a64b-79b3b86d28e3                  Grid  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##2b35c4e0-d85f-44b7-9e2c-4a110f9944a3      SubstatSeriesImp  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##42a937f4-fd79-4d57-8153-14d40107b23a           SubstatMain  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##43fd1008-34f6-4721-a468-64339d340cff        SubstatTr2tap5  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##95d267b2-3ee1-4a9d-a400-36bfb8032412            SubstatTr2  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##a598110a-4286-44e1-8335-56c866363cd7           SubstatLine  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##c9ce2b09-1225-4afa-bf85-9284fdb1f415           SubstatTr3a  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##eba981b5-0007-40bb-8f5c-f14c277f5d61           SubstatTr3b  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion
##f4637966-e63c-4bb4-89ed-0f897e40b05c          SubstatEqLne  2fdc1414-2e27-46c9-9989-860d4f8d420b  SubGeographicalRegion














    # for quick export of data use data[data.VALUE == "PowerTransformer"].to_csv(export.csv) or data[data.VALUE == "PowerTransformer"].to_clipboard() and  paste to excel, for other method refer to pandas manual


    #data = load_RDF_to_dataframe(r"C:\Users\kristjan.vilgo\Desktop\IGM_hour23\IGM_hour23\20180310T2330Z_2D_ELERING_TP_001.xml")